import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-nt", action="store", dest="nt_dir")
args = parser.parse_args()

out = open(f"{args.nt_dir}/wikidata.nt", "w")

for i in range(8):
    print(i)
    line = " "
    fl = open(f"{args.nt_dir}/wikidata_{i}.nt", "r")
    while line:
        line = fl.readline()
        line = line.strip()
        if line:
            out.write(line + "\n")

out.close()
print("finished")
