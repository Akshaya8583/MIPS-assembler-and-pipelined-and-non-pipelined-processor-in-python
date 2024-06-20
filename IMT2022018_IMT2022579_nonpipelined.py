class NonPipelinedProcessor:
    opcodes = {
        "000000": "R", 
        "000101": "bne", 
        "000100": "beq",
        "000010": "j", 
	    "001111": "lui",
	    "001101": "ori",
        "001000": "addi",
        "100011": "lw",
        "101011": "sw",
    }

    registers = {i + 16: f"$s{i}" for i in range(8)} | {i + 8: f"$t{i}" for i in range(8)} | {24: "$t8", 25: "$t9", 0: "$zero", 4: "$a0"}

    def __init__(self, start_address, IMem, RegFile = {}, MemFile = {}):
        self.clk = 0
        self.pc = start_address
        self.IMem = IMem
        self.RegFile = {x:0 for x in self.registers.values()} | RegFile
        self.MemFile = MemFile

    def instruction_fetch(self):
        return self.IMem[self.pc]

    def instruction_decode(self, instruction):
        data = {}
        opcode = instruction[0:6]
        data["type"] = self.opcodes[opcode]

        if self.opcodes[opcode] in ("j", "jal", "bne", "beq"):
            data["control"] = {"RegWrite": 0, "RegDst": 0, "ALUSrc": 1, "MemWrite": 0, "MemRead": 0, "MemtoReg": 0, "Branch": 1}

        elif self.opcodes[opcode] == "R":
            data["control"] = {"RegWrite": 1, "RegDst": 1, "ALUSrc": 0, "MemWrite": 0, "MemRead": 0, "MemtoReg": 0, "Branch": 0}

        elif self.opcodes[opcode] == "lw":
            data["control"] = {"RegWrite": 1, "RegDst": 0, "ALUSrc": 1, "MemWrite": 0, "MemRead": 1, "MemtoReg": 1, "Branch": 0}
    
        elif self.opcodes[opcode] == "sw":
            data["control"] = {"RegWrite": 0, "RegDst": 0, "ALUSrc": 1, "MemWrite": 1, "MemRead": 0, "MemtoReg": 0, "Branch": 0}

        elif self.opcodes[opcode] in ("lui", "ori", "addi"):
            data["control"] = {"RegWrite": 1, "RegDst": 0, "ALUSrc": 1, "MemWrite": 0, "MemRead": 0, "MemtoReg": 0, "Branch": 0}

        if self.opcodes[opcode] == "j":
            data["target"] = int(instruction[6:32] + "00", 2)
            return data

        data["rs"] =  instruction[6:11]
        data["rt"] =  instruction[11:16]

        if data["control"]["RegDst"]:
            data["rd"] = instruction[16:21]
            data["shamt"] = instruction[21:26]
            data["funct"] = instruction[26:32]

        elif instruction[16] == "1":
            data["imm"] = - int("".join(("1" if bit == "0" else "0") for bit in instruction[16:32]), 2) - 1

        else:
            data["imm"] = int(instruction[16:32], 2)

        return data    
    
    def execute(self, data, ALUSrc):
        source1 = self.RegFile[self.registers[int(data["rs"], 2)]]
        source2 = self.RegFile[self.registers[int(data["rt"], 2)]] if data["control"]["RegDst"] or data["type"] in ("beq", "bne") else data["imm"]

        if data["type"] in ("lw", "sw", "addi") or data.get("funct") == "100000":
            return source1 + source2
        elif data["type"] == "ori":
            return source1 | source2
        elif data.get("funct") == "100010":
            return source1 - source2
        elif data.get("funct") == "101010":
            return int(source1 < source2)
        elif data.get("funct") == "000000":
            return source2 << int(data["shamt"], 2)
        elif data["type"] == "bne" and source1 != source2:
            self.pc += data["imm"] * 4
        elif data["type"] == "beq" and source1 == source2:
            self.pc += data["imm"] * 4
        elif data["type"] == "j":
            self.pc = data["target"]
        elif data["type"] == "lui":
            return source2 * 2 ** 16

    def memory_access(self, location, MemRead, MemWrite, reg):
        if MemRead: return self.MemFile[location]
        elif MemWrite: self.MemFile[location] = self.RegFile[self.registers[int(reg, 2)]]

    def writeback(self, reg_dest, RegWrite, MemtoReg, ALUResult, MemVal):
        if RegWrite: 
            if MemtoReg: self.RegFile[self.registers[int(reg_dest, 2)]] = MemVal
            else: self.RegFile[self.registers[int(reg_dest, 2)]] = ALUResult

    def execute_binary_instruction(self):
        instr = self.instruction_fetch()
        self.clk += 1
        data = self.instruction_decode(instr)
        self.clk += 1
        result = self.execute(data, data["control"]["ALUSrc"])
        self.clk += 1
        mem_val = self.memory_access(result, data["control"]["MemRead"], data["control"]["MemWrite"], data["rs"] if data["control"]["MemRead"] else data["rt"])
        self.clk += 1
        self.writeback(data["rd"] if data["control"]["RegDst"] else data["rt"], data["control"]["RegWrite"], data["control"]["MemtoReg"], result, mem_val)
        self.clk += 1

    def execute_binary_code(self):
        while True:
            try:
                self.execute_binary_instruction()
                self.pc += 4

            except:      
                print(f"{self.clk} clock cycles")
                return self.MemFile, self.RegFile
            

start_address = 4194304

print("Factorial:")
with open("IMT2022018_IMT2022579_factorial_output.txt") as f:
    code = f.readlines()

reg = {"$t0": int(input("Enter a number: "))}
IMem = {start_address + 4 * linenum: line.strip("\n") for linenum, line in enumerate(code)}
processor1 = NonPipelinedProcessor(start_address, IMem, reg)
print("Output:", processor1.execute_binary_code()[1]["$t2"])

print("Fibonacci:")
with open("IMT2022018_IMT2022579_fibonacci_output.txt") as f:
    code = f.readlines()

reg = {"$s1": int(input("Enter a number: "))}
IMem = {start_address + 4 * linenum: line.strip("\n") for linenum, line in enumerate(code)}
processor = NonPipelinedProcessor(start_address, IMem, reg)
print("Output:", processor.execute_binary_code()[1]["$t2"])