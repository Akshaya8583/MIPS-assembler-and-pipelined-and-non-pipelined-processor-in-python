lui $s5, 0
ori $s5, $s5, 0 
sub $s6, $t1, $zero
addi $t8, $t2, 0
addi $t9, $t3, 0
addi $a0, $a0, 1
main:
	addi $s3, $t1, 0  #arr_len(n)
	addi  $t0, $t2, 0  #first element addr
	lui $s1, 0
	ori $s1, $s1, 0  #i = 0
	lui $s2, 0
	ori $s2, $s2, 0  #j = 0
	sub $s4, $t1, $a0 # n-1
for:
	sll $t7, $s2, 2  # counter going to the next element
	add $t7, $t0, $t7 #going to the address of next element
	add $t8, $t8, $zero
	add $t9, $t9, $zero
	lw $t4, 0($t7)   #arr[j]
	lw $t5, 4($t7)    #arr[j+1]
	slt $t6, $t4, $t5               #if t4 < t5
	bne $t6, $zero, increment
	sw $t4, 4($t7)
	sw $t5, 0($t7)        #swap
increment:
	addi $s2, $s2, 1     #j + 1
	sub $s3, $s4, $s1    #n - i - 1	
	bne $s2, $s4, for   #if j not equal to n - 1 go to loop
	addi $s1, $s1, 1     #else i + 1
	lui $s2, 0
	ori $s2, $s2, 0      #and reset j to 0
	bne $s1, $s4, for