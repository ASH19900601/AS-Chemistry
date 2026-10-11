# IGCSE / AS-level algorithms written in Python the way Cambridge mark schemes write them.
#
# These are original teaching examples, not official answers. Each subprogram names the
# mark-scheme (MS) pattern it follows, so the pseudocode can be read side by side.
# Arrays are Python lists indexed from 0, as in the 9618 Paper 4 Python answers;
# the comment on each declaration states the valid index range.

import random

# CONSTANT
MaxScore = 100


def InputScore():
    # Input validation: REPEAT ... UNTIL Score >= 0 AND Score <= MaxScore
    # Python has no post-condition loop, so a Valid flag is set to FALSE before the loop
    # (the form used in 9608_s18_ms_22 GetNumber and 9618_s24_ms_41 Initialise).
    # DECLARE Score : INTEGER
    # DECLARE Valid : BOOLEAN
    Valid = False
    while Valid == False:
        try:
            Score = int(input("Enter a score from 0 to " + str(MaxScore) + ": "))
            if Score >= 0 and Score <= MaxScore:
                Valid = True
            else:
                print("The score must be from 0 to", MaxScore)
        except ValueError:
            print("Please enter a whole number")
    return Score


def CalculateAverage(Scores, NumberOfScores):
    # Totalling then averaging (0478 Paper 2, e.g. 0478_m23_ms_22 p5).
    # Scores : ARRAY[0:NumberOfScores - 1] OF INTEGER
    # DECLARE Total : INTEGER
    # DECLARE Index : INTEGER
    if NumberOfScores == 0:
        return 0.0
    Total = 0
    for Index in range(0, NumberOfScores):
        Total = Total + Scores[Index]
    return Total / NumberOfScores


def FindHighestPosition(Scores, NumberOfScores):
    # Highest value, initialised from the first element (9608_s18_ms_21 ProcessMarks,
    # 0478_s24_ms_22 p8). Returns the position of the first highest score, or -1 if empty.
    # DECLARE Highest, Position, Index : INTEGER
    if NumberOfScores == 0:
        return -1
    Highest = Scores[0]
    Position = 0
    for Index in range(1, NumberOfScores):
        if Scores[Index] > Highest:
            Highest = Scores[Index]
            Position = Index
    return Position


def CountAbove(Scores, NumberOfScores, Limit):
    # Counting (0478_w20_ms_22 p7: Higher <- Higher + 1).
    # DECLARE Count, Index : INTEGER
    Count = 0
    for Index in range(0, NumberOfScores):
        if Scores[Index] > Limit:
            Count = Count + 1
    return Count


def LinearSearch(Names, NumberOfNames, SearchName):
    # Linear search with a flag: WHILE Index <= Max AND Found = FALSE
    # (9608_w20_ms_21 GetIndex, 9618_s22_ms_22 Exists). Returns the index or -1.
    # DECLARE Index : INTEGER
    # DECLARE Found : BOOLEAN
    Index = 0
    Found = False
    while Index < NumberOfNames and Found == False:
        if Names[Index] == SearchName:
            Found = True
        else:
            Index = Index + 1
    if Found == False:
        Index = -1
    return Index


def BubbleSort(Values, NumberOfValues):
    # Bubble sort exactly as the AS mark schemes write it: REPEAT ... UNTIL NoSwaps = TRUE,
    # with a Boundary that shrinks after each pass (9608_w20_ms_23, 9618_s25_ms_21 Sort).
    # This is a procedure: it changes the list that is passed in and returns nothing.
    # DECLARE Temp : INTEGER
    # DECLARE NoSwaps : BOOLEAN
    # DECLARE Boundary, Index : INTEGER
    Boundary = NumberOfValues - 1
    NoSwaps = False
    while NoSwaps == False:            # REPEAT
        NoSwaps = True
        for Index in range(0, Boundary):
            if Values[Index] > Values[Index + 1]:
                Temp = Values[Index]
                Values[Index] = Values[Index + 1]
                Values[Index + 1] = Temp
                NoSwaps = False
        Boundary = Boundary - 1        # UNTIL NoSwaps = TRUE


def CountVowels(Text):
    # Character-by-character loop: ThisChar <- LCASE(MID(Text, Index, 1))
    # Python strings start at position 0, so MID(Text, Index + 1, 1) is Text[Index].
    # DECLARE Count, Index : INTEGER
    # DECLARE ThisChar : CHAR
    Count = 0
    for Index in range(0, len(Text)):
        ThisChar = Text[Index].lower()
        if ThisChar == "a" or ThisChar == "e" or ThisChar == "i" or ThisChar == "o" or ThisChar == "u":
            Count = Count + 1
    return Count


def IsPalindrome(InString):
    # 9618_s22_ms_21 IsPalindrome, translated line by line.
    # DECLARE IsPal : BOOLEAN
    # DECLARE Index, Num : INTEGER
    # DECLARE CharA, CharB : CHAR
    IsPal = True
    Index = 0
    Num = len(InString) // 2                 # INT(LENGTH(InString) / 2)
    while Index < Num and IsPal == True:
        CharA = InString[Index]
        CharB = InString[len(InString) - Index - 1]
        if CharA.upper() != CharB.upper():
            IsPal = False
        Index = Index + 1
    return IsPal


def SplitName(FullName):
    # Pseudocode: PROCEDURE SplitName(FullName : STRING, BYREF FirstName, LastName : STRING)
    # Python cannot change the caller's string variables, so both results are returned
    # together and unpacked by the caller (as 9618_s22_ms_41 Enqueue returns several values):
    #     FirstName, LastName = SplitName("Ada Lovelace")
    # DECLARE Index : INTEGER
    # DECLARE FirstName, LastName : STRING
    Index = 0
    while Index < len(FullName) and FullName[Index] != " ":
        Index = Index + 1
    FirstName = FullName[0:Index]            # LEFT(FullName, Index)
    LastName = FullName[Index + 1:]          # RIGHT(FullName, LENGTH(FullName) - Index - 1)
    return FirstName, LastName


def ChangeSupplier(OldFileName, NewFileName, Code1, Code2):
    # Text file copy with changes (9618_s23_ms_23 ChangeSupp). Each line holds a 4-character
    # item number, a 3-character supplier code and a description. Returns the number of
    # lines changed, or -1 if the old file cannot be opened.
    # DECLARE Count : INTEGER
    # DECLARE ThisLine, ThisCode : STRING
    try:
        OldFile = open(OldFileName, "r")
    except IOError:
        print("Could not open the file", OldFileName)
        return -1
    try:
        NewFile = open(NewFileName, "w")
    except IOError:
        print("Could not create the file", NewFileName)
        OldFile.close()
        return -1
    Count = 0
    ThisLine = OldFile.readline()
    while ThisLine != "":                    # WHILE NOT EOF(OldFileName)
        ThisLine = ThisLine.rstrip("\n")     # remove only the end-of-line character
        ThisCode = ThisLine[4:7]             # MID(ThisLine, 5, 3)
        if ThisCode == Code1:
            ThisLine = ThisLine[0:4] + Code2 + ThisLine[7:]   # LEFT(ThisLine, 4) & Code2 & RIGHT(...)
            Count = Count + 1
        NewFile.write(ThisLine + "\n")       # WRITEFILE NewFileName, ThisLine
        ThisLine = OldFile.readline()        # READFILE OldFileName, ThisLine
    OldFile.close()
    NewFile.close()
    return Count


def ReadLines(FileName):
    # 9618 Paper 4 file reading: open inside try ... except IOError, then for Line in File
    # (9618_s23_ms_41, 9618_w23_ms_41 ReadData). Returns a list of lines without "\n".
    # DECLARE Lines : ARRAY OF STRING
    Lines = []
    try:
        File = open(FileName, "r")
    except IOError:
        print("Could not find file", FileName)
        return Lines
    for Line in File:
        Lines.append(Line.rstrip("\n"))
    File.close()
    return Lines


def RollDice(NoOfTimes):
    # 9618_s25_ms_23 RollDice: RollValue <- INT(RAND(6)) + 1
    # random.randint(1, 6) includes both 1 and 6.
    # DECLARE RollValue, Count, Sum : INTEGER
    if NoOfTimes <= 0:
        return 0.0
    Sum = 0
    for Count in range(0, NoOfTimes):
        RollValue = random.randint(1, 6)
        Sum = Sum + RollValue
    return Sum / NoOfTimes
