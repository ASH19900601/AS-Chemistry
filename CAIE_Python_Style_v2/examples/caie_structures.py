# A Level (Paper 3/4) data structures written the way 9618 Paper 4 Python answers write them:
# module-level arrays and pointers declared once, `global` statements inside the
# subprograms that change them, explicit pointer arithmetic, and classes with private
# attributes plus Get/Set methods.
#
# These are original teaching examples, not official answers. Lists are indexed from 0.

# ---------------------------------------------------------------- stack (9618_s25_ms_42)
# CONSTANT
StackSize = 10
# DECLARE Stack : ARRAY[0:9] OF INTEGER
# DECLARE TopOfStack : INTEGER        (-1 means the stack is empty)
Stack = [0 for Index in range(StackSize)]
TopOfStack = -1


def InitialiseStack():
    global Stack
    global TopOfStack
    for Index in range(0, StackSize):
        Stack[Index] = 0
    TopOfStack = -1


def Push(DataToPush):
    # Returns TRUE if the item was added, FALSE if the stack is full.
    global Stack
    global TopOfStack
    if TopOfStack == StackSize - 1:
        return False
    else:
        TopOfStack = TopOfStack + 1
        Stack[TopOfStack] = DataToPush
        return True


def Pop():
    # Returns the top item, or -1 if the stack is empty (the stack holds values >= 0).
    global Stack
    global TopOfStack
    if TopOfStack == -1:
        return -1
    else:
        ReturnValue = Stack[TopOfStack]
        TopOfStack = TopOfStack - 1
        return ReturnValue


# ------------------------------------------------------- circular queue (9618_s25_ms_41)
# CONSTANT
QueueSize = 5
# DECLARE Queue : ARRAY[0:4] OF STRING
# DECLARE HeadPointer, TailPointer, NumberItems : INTEGER
Queue = ["" for Index in range(QueueSize)]
HeadPointer = 0
TailPointer = -1
NumberItems = 0


def InitialiseQueue():
    global Queue
    global HeadPointer
    global TailPointer
    global NumberItems
    for Index in range(0, QueueSize):
        Queue[Index] = ""
    HeadPointer = 0
    TailPointer = -1
    NumberItems = 0


def Enqueue(InputData):
    global Queue
    global TailPointer
    global NumberItems
    if NumberItems == QueueSize:
        return False
    TailPointer = TailPointer + 1
    if TailPointer == QueueSize:          # wrap round to the start of the array
        TailPointer = 0
    Queue[TailPointer] = InputData
    NumberItems = NumberItems + 1
    return True


def Dequeue():
    # Returns the item at the head, or "" if the queue is empty.
    global Queue
    global HeadPointer
    global NumberItems
    if NumberItems == 0:
        return ""
    ReturnValue = Queue[HeadPointer]
    HeadPointer = HeadPointer + 1
    if HeadPointer == QueueSize:
        HeadPointer = 0
    NumberItems = NumberItems - 1
    return ReturnValue


# ------------------------------------- linked list in an array with a free list (9618_w24_ms_41)
# CONSTANT
ListSize = 20
NullPointer = -1
# DECLARE LinkedList : ARRAY[0:19, 0:1] OF INTEGER   column 0 = data, column 1 = next pointer
# DECLARE FirstNode, FirstEmpty : INTEGER
LinkedList = [[-1, -1] for Index in range(ListSize)]
FirstNode = NullPointer
FirstEmpty = 0


def InitialiseList():
    global LinkedList
    global FirstNode
    global FirstEmpty
    for Index in range(0, ListSize):
        LinkedList[Index][0] = -1
        LinkedList[Index][1] = Index + 1          # every node points to the next free node
    LinkedList[ListSize - 1][1] = NullPointer
    FirstNode = NullPointer
    FirstEmpty = 0


def InsertAtFront(NewData):
    # Takes the first free node, stores the data and links it in front of the list.
    global LinkedList
    global FirstNode
    global FirstEmpty
    if FirstEmpty == NullPointer:
        return False
    NewNode = FirstEmpty
    FirstEmpty = LinkedList[NewNode][1]
    LinkedList[NewNode][0] = NewData
    LinkedList[NewNode][1] = FirstNode
    FirstNode = NewNode
    return True


def RemoveData(ItemToRemove):
    # Unlinks the first node holding ItemToRemove and returns it to the free list.
    global LinkedList
    global FirstNode
    global FirstEmpty
    CurrentPointer = FirstNode
    PreviousPointer = NullPointer
    while CurrentPointer != NullPointer and LinkedList[CurrentPointer][0] != ItemToRemove:
        PreviousPointer = CurrentPointer
        CurrentPointer = LinkedList[CurrentPointer][1]
    if CurrentPointer == NullPointer:
        return False
    if PreviousPointer == NullPointer:
        FirstNode = LinkedList[CurrentPointer][1]
    else:
        LinkedList[PreviousPointer][1] = LinkedList[CurrentPointer][1]
    LinkedList[CurrentPointer][0] = -1
    LinkedList[CurrentPointer][1] = FirstEmpty
    FirstEmpty = CurrentPointer
    return True


def ListToString():
    # Follows the pointers from FirstNode and joins the data items with spaces.
    Output = ""
    CurrentPointer = FirstNode
    while CurrentPointer != NullPointer:
        Output = Output + str(LinkedList[CurrentPointer][0]) + " "
        CurrentPointer = LinkedList[CurrentPointer][1]
    return Output


# ------------------------------- binary tree in a 2D array (9618_w21_ms_41, 9618_w25_ms_42)
# CONSTANT
TreeSize = 20
# DECLARE TreeArray : ARRAY[0:19, 0:2] OF INTEGER   [LeftPointer, Data, RightPointer]
# DECLARE RootPointer, FreeNode : INTEGER
TreeArray = [[-1, -1, -1] for Index in range(TreeSize)]
RootPointer = -1
FreeNode = 0


def InitialiseTree():
    global TreeArray
    global RootPointer
    global FreeNode
    for Index in range(0, TreeSize):
        TreeArray[Index][0] = -1
        TreeArray[Index][1] = -1
        TreeArray[Index][2] = -1
    RootPointer = -1
    FreeNode = 0


def AddNode(NodeData):
    global TreeArray
    global RootPointer
    global FreeNode
    if FreeNode >= TreeSize:
        print("The tree is full")
        return False
    TreeArray[FreeNode][0] = -1
    TreeArray[FreeNode][1] = NodeData
    TreeArray[FreeNode][2] = -1
    if RootPointer == -1:
        RootPointer = FreeNode
    else:
        Placed = False
        CurrentNode = RootPointer
        while Placed == False:
            if NodeData < TreeArray[CurrentNode][1]:
                if TreeArray[CurrentNode][0] == -1:
                    TreeArray[CurrentNode][0] = FreeNode
                    Placed = True
                else:
                    CurrentNode = TreeArray[CurrentNode][0]
            else:
                if TreeArray[CurrentNode][2] == -1:
                    TreeArray[CurrentNode][2] = FreeNode
                    Placed = True
                else:
                    CurrentNode = TreeArray[CurrentNode][2]
    FreeNode = FreeNode + 1
    return True


def InOrder(RootNode):
    # Recursive in-order traversal: left subtree, node, right subtree.
    if RootNode == -1:
        return
    InOrder(TreeArray[RootNode][0])
    print(TreeArray[RootNode][1])
    InOrder(TreeArray[RootNode][2])


# ------------------------------------------------- sorting and searching (9618_s25_ms_43)
def InsertionSort(DataArray, NumberOfItems):
    # DECLARE CurrentValue, Position, Index : INTEGER
    for Index in range(1, NumberOfItems):
        CurrentValue = DataArray[Index]
        Position = Index - 1
        while Position >= 0 and DataArray[Position] > CurrentValue:
            DataArray[Position + 1] = DataArray[Position]
            Position = Position - 1
        DataArray[Position + 1] = CurrentValue


def BinarySearch(DataArray, NumberOfItems, ItemToFind):
    # Iterative binary search on a sorted array. Returns the index or -1.
    # DECLARE Low, High, Middle : INTEGER
    Low = 0
    High = NumberOfItems - 1
    while Low <= High:
        Middle = (Low + High) // 2              # (Low + High) DIV 2
        if DataArray[Middle] < ItemToFind:
            Low = Middle + 1
        elif DataArray[Middle] > ItemToFind:
            High = Middle - 1
        else:
            return Middle
    return -1


def RecursiveBinarySearch(DataArray, Lower, Upper, DataToFind):
    # 9618_w25_ms_42: the base case is an empty range (Upper < Lower).
    if Upper < Lower:
        return -1
    Middle = Lower + (Upper - Lower) // 2
    if DataArray[Middle] == DataToFind:
        return Middle
    elif DataArray[Middle] > DataToFind:
        return RecursiveBinarySearch(DataArray, Lower, Middle - 1, DataToFind)
    else:
        return RecursiveBinarySearch(DataArray, Middle + 1, Upper, DataToFind)


# -------------------------------------------- hash table with linear probing (9608_s20_ms_41)
# CONSTANT
TableSize = 11
# DECLARE HashTable : ARRAY[0:10] OF INTEGER    (-1 marks an empty slot)
HashTable = [-1 for Index in range(TableSize)]


def Hash(Key):
    return Key % TableSize                          # Key MOD TableSize


def InsertKey(Key):
    # Returns the index used, or -1 if the table is full.
    global HashTable
    Index = Hash(Key)
    Count = 0
    while HashTable[Index] != -1 and Count < TableSize:
        Index = Index + 1
        if Index == TableSize:
            Index = 0
        Count = Count + 1
    if Count == TableSize:
        return -1
    HashTable[Index] = Key
    return Index


def FindKey(Key):
    Index = Hash(Key)
    Count = 0
    while HashTable[Index] != Key and HashTable[Index] != -1 and Count < TableSize:
        Index = Index + 1
        if Index == TableSize:
            Index = 0
        Count = Count + 1
    if HashTable[Index] == Key:
        return Index
    return -1


# --------------------------------- classes, private attributes, inheritance (9618_s23_ms_41)
class Vehicle:
    # PRIVATE ID : STRING
    # PRIVATE MaxSpeed, CurrentSpeed, IncreaseAmount, HorizontalPosition : INTEGER
    def __init__(self, IDP, MaxSpeedP, IncreaseAmountP):
        self.__ID = IDP
        self.__MaxSpeed = MaxSpeedP
        self.__IncreaseAmount = IncreaseAmountP
        self.__CurrentSpeed = 0
        self.__HorizontalPosition = 0

    def GetID(self):
        return self.__ID

    def GetCurrentSpeed(self):
        return self.__CurrentSpeed

    def GetMaxSpeed(self):
        return self.__MaxSpeed

    def GetIncreaseAmount(self):
        return self.__IncreaseAmount

    def GetHorizontalPosition(self):
        return self.__HorizontalPosition

    def SetCurrentSpeed(self, NewSpeed):
        self.__CurrentSpeed = NewSpeed

    def SetHorizontalPosition(self, NewPosition):
        self.__HorizontalPosition = NewPosition

    def IncreaseSpeed(self):
        self.__CurrentSpeed = self.__CurrentSpeed + self.__IncreaseAmount
        if self.__CurrentSpeed > self.__MaxSpeed:
            self.__CurrentSpeed = self.__MaxSpeed
        self.__HorizontalPosition = self.__HorizontalPosition + self.__CurrentSpeed


class Helicopter(Vehicle):
    # PRIVATE VerticalPosition, VerticalChange, MaxHeight : INTEGER
    def __init__(self, IDP, MaxSpeedP, IncreaseAmountP, VerticalChangeP, MaxHeightP):
        super().__init__(IDP, MaxSpeedP, IncreaseAmountP)
        self.__VerticalPosition = 0
        self.__VerticalChange = VerticalChangeP
        self.__MaxHeight = MaxHeightP

    def GetVerticalPosition(self):
        return self.__VerticalPosition

    def IncreaseSpeed(self):
        # The parent's private attributes are reached through its Get/Set methods.
        self.__VerticalPosition = self.__VerticalPosition + self.__VerticalChange
        if self.__VerticalPosition > self.__MaxHeight:
            self.__VerticalPosition = self.__MaxHeight
        super().IncreaseSpeed()


# --------------------------- returning a record when a function has two results (9618_w24_ms_21)
class DivisionResult:
    # TYPE Result
    #    DECLARE Done : BOOLEAN
    #    DECLARE Value : REAL
    # ENDTYPE
    def __init__(self):
        self.Done = False
        self.Value = 0.0


def IsNumeric(Text):
    # IS_NUM(Text): TRUE if Text can be converted to a number.
    try:
        float(Text)
        return True
    except ValueError:
        return False


def Evaluate(NumStr1, NumStr2):
    # FUNCTION Evaluate(NumStr1, NumStr2 : STRING) RETURNS Result
    RetVal = DivisionResult()
    if IsNumeric(NumStr1) == True and IsNumeric(NumStr2) == True:
        Num1 = float(NumStr1)
        Num2 = float(NumStr2)
        if Num2 != 0:
            RetVal.Value = Num1 / Num2
            RetVal.Done = True
    return RetVal
