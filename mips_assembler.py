def decimal_to_binary(num, bits):
    if num < 0:
        return twos_complement(decimal_to_binary(-num, bits))
	
    s = ""

    while num:
        s += str(num % 2)
        num //= 2

    return "0" * (bits - len(s)) + s[::-1]

def twos_complement(binary_str):
    new_str = ""
    
    for i in binary_str:
        if i == "1": new_str += "0"
        else: new_str += "1"
        
    return bin(int(new_str, 2) + 1)[2:].zfill(len(new_str))

in_file = open("IMT2022018_IMT2022579_factorial.asm")
out_file = open("factorialoutput.txt", "w")

code = in_file.read()

opcodes = {
    "sll": "000000",
    "slt": "000000",
    "add": "000000",
    "mul": "000000",
    "sub": "000000",
	"lui": "001111",
	"ori": "001101",
    "addi": "001000",
    "lw": "100011",
    "sw": "101011",
    "bne": "000101"
}

i_format = ["addi", "ori", "lui"]
load_store_format = ["lw", "sw"]
r_format = {"add": "100000", "sub": "100010", "slt": "101010", "sll": "000000", "sub": "100010"}

registers = {f"$s{i}": i + 16 for i in range(8)} 
registers.update({f"$t{i}": i + 8 for i in range(8)})
registers.update({"$t8": 24, "$t9": 25, "$zero": 0, "$a0": 4})

code = code.replace("\t", "") # Removing tabspaces
code = code.replace(",", "") # Removing commas

for reg in registers:
    code = code.replace(reg, decimal_to_binary(registers[reg], 5)) 

code = [line[:line.find("#")] if "#" in line else line for line in code.split("\n")] # Removing comments

labels = {}

for ind, line in enumerate(code):
    if ":" in line:
        label_name = line[:line.find(":")]
        labels[label_name] = ind
        code.pop(ind)

code = [line.split() for line in code]

for ind, line in enumerate(code):
    if line[-1] in labels:
        offset = labels[line[-1]] - ind - 1
        line[-1] = decimal_to_binary(offset, 16)
        
    if line[0] in r_format:
        if line[0] == "sll":
            line.insert(1, "00000")
            line[-1] = decimal_to_binary(int(line[-1]), 5)
            line[2], line[3] = line[3], line[2]
        else:
            line.append(line.pop(1))
            line.append("00000")
        line.append(r_format[line[0]])
            
    elif line[0] in load_store_format:
        offset = int(line[-1][:line[-1].find("(")])
        addr = line[-1][line[-1].find("(") + 1: line[-1].find(")")]
        line.insert(1, addr)
        line[-1] = decimal_to_binary(offset, 16)
            
    elif line[0] in i_format:
        if line[0] == "lui": line.insert(1, "00000")
        else: line[1], line[2] = line[2], line[1]
        line[-1] = decimal_to_binary(int(line[-1]), 16)
		
    line[0] = opcodes[line[0]]
    code[ind] = "".join(line)
        
out_file.write("\n".join(code))
out_file.close()