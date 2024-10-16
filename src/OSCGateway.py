from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server, udp_client
import time
import numpy as np

class OSCGateway:
    def __init__(self, r_ip='', r_port=5005, 
                 s_ip='', s_ports=[6006, 7007, 8008],
                 xy_remap=False, yz_remap=False, zx_remap=False,
                 x_flip=False, y_flip=False, z_flip=False,
                 mic_xyz=(0., 0., 0.),
                 mic_rot_deg=(0., 0.),
                 verbose=False,
                 ):
        self.verbose = verbose
        # OSC
        self.clients = [udp_client.SimpleUDPClient(s_ip, port) for port in s_ports]
        dispatcher = Dispatcher()
        dispatcher.map('/pos1/xyz', self._send)
        dispatcher.map('/pos2/xyz', self._send)
        self.server = osc_server.ThreadingOSCUDPServer((r_ip, r_port), dispatcher)

        # Remap
        self.xy_remap, self.yz_remap, self.zx_remap = xy_remap, yz_remap, zx_remap
        # Flip
        self.x_flip, self.y_flip, self.z_flip = x_flip, y_flip, z_flip
        # 
        self.mic_xyz = mic_xyz
        self.mic_rot_deg = mic_rot_deg
    
    def _send(self, unused_addr, x, y, z):
        print('[INFO]', 'OSCGateway::_send:', unused_addr, f'x: {x:.2f} | y: {y:.2f} | z: {z:.2f}') if self.verbose else None
        if 'pos1' in unused_addr:
            id_src = 0
        elif 'pos2' in unused_addr:    
            id_src = 1
        else:
            print('ERROR')
        
        # Remap
        if self.xy_remap:
            x, y = y, x
        if self.yz_remap:
            y, z = z, y
        if self.zx_remap:
            z, x = x, z
        # Flip
        x = (-1)**self.x_flip * x
        y = (-1)**self.y_flip * y
        z = (-1)**self.z_flip * z

        # XYZ conversion
        scale = 10.
        x_relative = (x - self.mic_xyz[0]) / scale
        y_relative = (y - self.mic_xyz[1]) / scale
        z_relative = (z - self.mic_xyz[2]) / scale

        az_rot = np.deg2rad(self.mic_rot_deg[0])
        el_rot = np.deg2rad(self.mic_rot_deg[1])
        Rz_m = np.array([[np.cos(az_rot), -np.sin(az_rot), 0.],
                         [np.sin(az_rot), np.cos(az_rot), 0.],
                         [0., 0., 1.],
                         ])
        Ry_m = np.array([[np.cos(el_rot), 0., np.sin(el_rot)],
                         [0., 1., 0.],
                         [-np.sin(el_rot), 0., np.cos(el_rot)],
                         ])
        xyz_v = Ry_m @ Rz_m @ np.array([x_relative, y_relative, z_relative])
        x_relative = xyz_v[0]
        y_relative = xyz_v[1]
        z_relative = xyz_v[2]
        # Cart to Spherical
        azim = np.rad2deg(np.atan2(y_relative, x_relative))
        elev = np.rad2deg(np.arcsin(z_relative / np.sqrt(x_relative**2+y_relative**2+z_relative**2)))
        # 
        print('[INFO]', 'OSCGateway::_send:', unused_addr, f'az: {azim:.0f} | el: {elev:.0f}') if self.verbose else None
        # Send
        self.clients[id_src].send_message("/ProbeDecoder/azimuth", azim)
        self.clients[id_src].send_message("/ProbeDecoder/elevation", elev)

        self.clients[2].send_message(f"/MultiEncoder/azimuth{id_src}", azim)
        self.clients[2].send_message(f"/MultiEncoder/elevation{id_src}", elev)


        

if __name__ == "__main__":

    my_gateway = OSCGateway(r_ip='127.0.0.1', r_port=5005,
                            s_ip='127.0.0.1', s_ports=[6006, 7007, 8008],
                            )
    
    print("Serving on {}".format(my_gateway.server.server_address))
    my_gateway.server.serve_forever()
