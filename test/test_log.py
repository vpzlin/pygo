
file_path = '/esdata/test/11.log'

with open(file_path, 'w') as file:
    num = 1000
    val = 0
    while val <= num:
        file.write("{:x}\n".format(val).zfill(12))
        val += 1



