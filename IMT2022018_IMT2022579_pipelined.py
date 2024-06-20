class PipelinedProcessor:
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

    def instruction_fetch(self, pc):
        return self.IMem[pc]

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
    
    def execute(self, data, dependencies):
        ALUSrc = data["control"]["ALUSrc"]

        if self.registers[int(data["rs"], 2)] in dependencies:
            source1 = dependencies[self.registers[int(data["rs"], 2)]]
        else:
            source1 = self.RegFile[self.registers[int(data["rs"], 2)]]

        if data["control"]["RegDst"] or data["type"] in ("beq", "bne"):        
            if self.registers[int(data["rt"], 2)] in dependencies:
                source2 = dependencies[self.registers[int(data["rt"], 2)]]
            else:
                source2 = self.RegFile[self.registers[int(data["rt"], 2)]] 
        
        else: source2 = data["imm"]

        if data["type"] in ("lw", "sw", "addi") or data.get("funct") == "100000":
            return data, source1 + source2
        elif data["type"] == "ori":
            return data, source1 | source2
        elif data.get("funct") == "100010":
            return data, source1 - source2
        elif data.get("funct") == "101010":
            return data, int(source1 < source2)
        elif data.get("funct") == "000000":
            return data, source2 << int(data["shamt"], 2)
        elif data["type"] == "bne":
            return data, source1 != source2
        elif data["type"] == "beq":
            return data, source1 == source2
        elif data["type"] == "lui":
            return data, source2 * 2 ** 16

    def memory_access(self, data, location, dependencies):
        MemRead = data["control"]["MemRead"]
        MemWrite = data["control"]["MemWrite"]
        reg = data["rs"] if data["control"]["MemRead"] else data["rt"]

        if MemRead: 
            return location, self.MemFile[location], data
        elif MemWrite:
            if self.registers[int(reg, 2)] in dependencies:
                self.MemFile[location] = dependencies[self.registers[int(reg, 2)]]
            else:
                self.MemFile[location] = self.RegFile[self.registers[int(reg, 2)]]
        return location, None, data

    def writeback(self, ALUResult, MemVal, data):
        reg_dest = data["rd"] if data["control"]["RegDst"] else data["rt"]
        RegWrite = data["control"]["RegWrite"]
        MemtoReg = data["control"]["MemtoReg"]

        if RegWrite: 
            if MemtoReg: self.RegFile[self.registers[int(reg_dest, 2)]] = MemVal
            else: self.RegFile[self.registers[int(reg_dest, 2)]] = ALUResult

    def execute_binary_code(self):
        dependencies = {}
        if_instr = id_instr = ex_instr = mem_instr = wb_instr = None

        id_queue = []
        ex_queue = []
        mem_queue = []
        wb_queue = []

        while True:
            if if_instr is None: if_instr = self.pc
            if id_instr is None and len(id_queue): id_instr = id_queue.pop()
            if ex_instr is None and len(ex_queue): ex_instr = ex_queue.pop()
            if mem_instr is None and len(mem_queue): mem_instr = mem_queue.pop()
            if wb_instr is None and len(wb_queue): wb_instr = wb_queue.pop()

            if if_instr:
                try: 
                    if_result = self.instruction_fetch(if_instr)
                    id_queue.insert(0, if_result)

                except: 
                    if_instr = None
                
                if_instr = None

            if id_instr:
                id_result = self.instruction_decode(id_instr)
                ex_queue.insert(0, id_result)
                id_instr = None

            if wb_instr:
                self.writeback(wb_instr[0], wb_instr[1], wb_instr[2])

                try:
                    dependencies.pop(self.registers[int(wb_instr[2]["rd"] if wb_instr[2]["control"]["RegDst"] else wb_instr[2]["rt"], 2)])
                except:
                    pass

                wb_instr = None

            if ex_instr:
                output = self.execute(ex_instr, dependencies)

                if output[0]["control"]["RegWrite"]:
                    dependencies[self.registers[int(output[0]["rd"] if output[0]["control"]["RegDst"] else output[0]["rt"], 2)]] = output[1]

                if output[0]["control"]["Branch"] and output[1]:
                    self.pc += (output[0]["imm"] - 2) * 4
                    id_queue = []
                    ex_queue = []
                    if_instr = id_instr = ex_instr = None

                else:
                    mem_queue.insert(0, output)

                ex_instr = None

            if mem_instr:
                output = self.memory_access(mem_instr[0], mem_instr[1], dependencies)

                if output[2]["control"]["MemRead"]:
                    dependencies[self.registers[int(output[2]["rt"], 2)]] = output[1]

                wb_queue.insert(0, output)
                mem_instr = None

            self.clk += 1
            self.pc += 4

            if len(id_queue) == 0 and len(ex_queue) == 0 and len(mem_queue) == 0 and len(wb_queue) == 0:
                print(f"{self.clk} clock cycles")
                return self.MemFile, self.RegFile

start_address = 4194304

print("Factorial:")
with open("IMT2022018_IMT2022579_factorial_output.txt") as f:
    code = f.readlines()

reg = {"$t0": int(input("Enter a number: "))}
IMem = {start_address + 4 * linenum: line.strip("\n") for linenum, line in enumerate(code)}
processor1 = PipelinedProcessor(start_address, IMem, reg)
print("Output:", processor1.execute_binary_code()[1]["$t2"])

print("Fibonacci:")
with open("IMT2022018_IMT2022579_fibonacci_output.txt") as f:
    code = f.readlines()

reg = {"$s1": int(input("Enter a number: "))}
IMem = {start_address + 4 * linenum: line.strip("\n") for linenum, line in enumerate(code)}
processor = PipelinedProcessor(start_address, IMem, reg)
print("Output:", processor.execute_binary_code()[1]["$t2"])