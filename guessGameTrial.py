from numpy import random

a = random.randint(1,50)
print(a)

c = 0
while True :
    b = int(input())
    c+=1
    if b == a:
        if c==1:
            print("Whoa you guessed it right in the very first time !")
            print("Was it an insider job ?")
            print("Run again to play !")
            break
        
        if c>1 :
            print("And you got it man !")
            print("It took you %d turns" %c)
            print("Runcode again to play !")
            break


    if b != a:
        if abs(b-a) < 10:
            print("Up or down some digits and you are there !")
        elif 10<=abs(b-a)<=25:
            print("Push a little harder !")

        else:
            print("Way far off Bud")
