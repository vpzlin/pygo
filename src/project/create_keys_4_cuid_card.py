with open("C:\\GreenPark\\UserFile\\Desktop\\temp\\new_all_0.keys", "w") as file:
    v_min = 0
    v_max = 17592186044415
    val = v_min
    while val <= v_max:
        file.write("{:x}\n".format(val).zfill(12))
        val += 1

