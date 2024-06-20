main:
    addi $t5, $zero, 1
    addi $t1, $zero, 1
    addi $t2, $zero, 1
loop:
    addi $t3, $t1, 0
    addi $t4, $t2, 0
inner_loop:
    sub $t3, $t3, $t5
    add $t2, $t2, $t4
    bne $t3, $zero, inner_loop
addi $t1, $t1, 1    # Increment loop counter
bne $t1, $t0, loop  # Branch back to the loop if not done