from OSCGateway import OSCGateway


if __name__ == "__main__":

    my_gateway = OSCGateway(r_ip='127.0.0.1', r_port=5005,
                            s_ip='127.0.0.1', s_ports=[6006, 7007, 8008],
                            xy_remap=True, yz_remap=False, zx_remap=False,
                            x_flip=False, y_flip=True, z_flip=False,
                            mic_xyz=(-5., 0., 0.),  # x, y, z (our convention, in meter)
                            mic_rot_deg=(0., 0.),  # azim, elev (in degree)
                            verbose=True,
                            )
    
    print("Listening on {}".format(my_gateway.server.server_address))
    my_gateway.server.serve_forever()
