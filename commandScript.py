import os

def something():
    x = 2
    return "something happened!!!"

def two():
    return "You entered two"

def user():
    return "This is when it would return the username"

def quit():
    print "Exiting MirrorScript"
    os._exit(0)

def startScriptConsole():
    while(True):
        userInput = raw_input("MirrorScript$ ")
        switcher = {
        "1": something,
        "2": two,
        "user": user,
        "quit": quit,
        "q": quit,
        }
        #print switcher.get(userInput, "Invalid")
        func = switcher.get(userInput, lambda: "Invalid month")
        print func()


if __name__ == '__main__':
    startScriptConsole()
    os._exit(0)