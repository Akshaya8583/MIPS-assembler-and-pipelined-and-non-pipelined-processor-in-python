addi $t4, $zero, -2
add $s1, $t4, $s1
addi $t1, $zero, 1
addi $t2, $zero, 1
addi $t3, $zero, 0
loop:
	addi $t3, $t3, 1
	addi $t4, $t1, 0
	addi $t1, $t2, 0
	add $t2, $t4, $t2
	bne $t3, $s1, loop