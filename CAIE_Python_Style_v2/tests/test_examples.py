# Behaviour tests for the teaching examples. Tests may use ordinary Python built-ins
# (sorted, in) as independent references; the examples themselves do not.
# Run from the CAIE_Python_Style_v2 folder:  python -m unittest discover -s tests -v

import contextlib
import io
import os
import random
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examples'))

import caie_basics as Basics          # noqa: E402
import caie_structures as Structures  # noqa: E402


class TestBasics(unittest.TestCase):

    def test_input_score_repeats_until_valid(self):
        Answers = ['abc', '150', '-1', '42']
        with mock.patch('builtins.input', side_effect=Answers):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(Basics.InputScore(), 42)

    def test_average_and_empty_array(self):
        self.assertEqual(Basics.CalculateAverage([4, 6, 8, 0], 3), 6.0)   # only 3 items are valid
        self.assertEqual(Basics.CalculateAverage([], 0), 0.0)

    def test_highest_position(self):
        self.assertEqual(Basics.FindHighestPosition([3, 9, 2, 9], 4), 1)  # first highest
        self.assertEqual(Basics.FindHighestPosition([-5, -2, -9], 3), 1)  # negatives work
        self.assertEqual(Basics.FindHighestPosition([], 0), -1)

    def test_count_above(self):
        self.assertEqual(Basics.CountAbove([10, 60, 70, 50], 4, 50), 2)

    def test_linear_search(self):
        Names = ['Ali', 'Bea', 'Cy', 'Bea']
        self.assertEqual(Basics.LinearSearch(Names, 4, 'Bea'), 1)
        self.assertEqual(Basics.LinearSearch(Names, 4, 'Dan'), -1)
        self.assertEqual(Basics.LinearSearch(Names, 1, 'Bea'), -1)       # respects the logical size
        self.assertEqual(Basics.LinearSearch([], 0, 'Ali'), -1)

    def test_bubble_sort_against_reference(self):
        Generator = random.Random(7)
        for Size in range(0, 12):
            Values = [Generator.randint(-20, 20) for Count in range(Size)]
            Expected = sorted(Values)
            Basics.BubbleSort(Values, Size)
            self.assertEqual(Values, Expected)

    def test_bubble_sort_only_sorts_logical_size(self):
        Values = [3, 1, 2, 0, -5]
        Basics.BubbleSort(Values, 3)
        self.assertEqual(Values, [1, 2, 3, 0, -5])

    def test_strings(self):
        self.assertEqual(Basics.CountVowels('Programming Is Fun'), 5)
        self.assertTrue(Basics.IsPalindrome('Level'))
        self.assertTrue(Basics.IsPalindrome(''))
        self.assertFalse(Basics.IsPalindrome('Python'))
        self.assertEqual(Basics.SplitName('Ada Lovelace'), ('Ada', 'Lovelace'))
        self.assertEqual(Basics.SplitName('Plato'), ('Plato', ''))

    def test_change_supplier_and_read_lines(self):
        with tempfile.TemporaryDirectory() as Folder:
            OldName = os.path.join(Folder, 'Stock.txt')
            NewName = os.path.join(Folder, 'NewStock.txt')
            with open(OldName, 'w') as File:
                File.write('0001ABCWidget  \n0002XYZBolt\n0003ABCNut\n')
            Count = Basics.ChangeSupplier(OldName, NewName, 'ABC', 'QQQ')
            self.assertEqual(Count, 2)
            self.assertEqual(Basics.ReadLines(NewName),
                             ['0001QQQWidget  ', '0002XYZBolt', '0003QQQNut'])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(Basics.ChangeSupplier(os.path.join(Folder, 'Missing.txt'), NewName, 'A', 'B'), -1)
                BadTarget = os.path.join(Folder, 'NoSuchFolder', 'Out.txt')
                self.assertEqual(Basics.ChangeSupplier(OldName, BadTarget, 'A', 'B'), -1)
                self.assertEqual(Basics.ReadLines(os.path.join(Folder, 'Missing.txt')), [])

    def test_roll_dice_range(self):
        random.seed(1)
        Average = Basics.RollDice(600)
        self.assertTrue(1 <= Average <= 6)
        self.assertEqual(Basics.RollDice(0), 0.0)


class TestStructures(unittest.TestCase):

    def test_stack_capacity_and_lifo(self):
        Structures.InitialiseStack()
        self.assertEqual(Structures.Pop(), -1)
        for Value in range(0, Structures.StackSize):
            self.assertTrue(Structures.Push(Value))
        self.assertFalse(Structures.Push(99))
        self.assertEqual(Structures.Pop(), Structures.StackSize - 1)
        self.assertEqual(Structures.Pop(), Structures.StackSize - 2)

    def test_circular_queue_wraps(self):
        Structures.InitialiseQueue()
        self.assertEqual(Structures.Dequeue(), '')
        for Letter in 'ABCDE':
            self.assertTrue(Structures.Enqueue(Letter))
        self.assertFalse(Structures.Enqueue('F'))
        self.assertEqual(Structures.Dequeue(), 'A')
        self.assertEqual(Structures.Dequeue(), 'B')
        self.assertTrue(Structures.Enqueue('F'))     # uses a slot at the start of the array
        self.assertTrue(Structures.Enqueue('G'))
        Output = ''
        for Count in range(0, 5):
            Output = Output + Structures.Dequeue()
        self.assertEqual(Output, 'CDEFG')

    def test_linked_list_insert_remove_and_reuse(self):
        Structures.InitialiseList()
        for Value in [5, 10, 15]:
            self.assertTrue(Structures.InsertAtFront(Value))
        self.assertEqual(Structures.ListToString(), '15 10 5 ')
        self.assertTrue(Structures.RemoveData(10))
        self.assertFalse(Structures.RemoveData(99))
        self.assertEqual(Structures.ListToString(), '15 5 ')
        FreedNode = Structures.FirstEmpty
        self.assertTrue(Structures.InsertAtFront(20))
        self.assertEqual(Structures.FirstNode, FreedNode)          # freed node is reused
        self.assertTrue(Structures.RemoveData(20))                 # removing the first node
        self.assertEqual(Structures.ListToString(), '15 5 ')

    def test_linked_list_full(self):
        Structures.InitialiseList()
        for Value in range(0, Structures.ListSize):
            self.assertTrue(Structures.InsertAtFront(Value))
        self.assertFalse(Structures.InsertAtFront(100))

    def test_binary_tree_in_order(self):
        Structures.InitialiseTree()
        for Value in [50, 30, 70, 20, 40, 60, 80, 30]:
            Structures.AddNode(Value)
        Buffer = io.StringIO()
        with contextlib.redirect_stdout(Buffer):
            Structures.InOrder(Structures.RootPointer)
        Printed = [int(Line) for Line in Buffer.getvalue().split()]
        self.assertEqual(Printed, sorted([50, 30, 70, 20, 40, 60, 80, 30]))

    def test_insertion_sort_and_searches(self):
        Generator = random.Random(3)
        for Size in range(0, 15):
            Data = [Generator.randint(0, 50) for Count in range(Size)]
            Expected = sorted(Data)
            Structures.InsertionSort(Data, Size)
            self.assertEqual(Data, Expected)
            for Target in range(-1, 52):
                Position = Structures.BinarySearch(Data, Size, Target)
                RecursivePosition = Structures.RecursiveBinarySearch(Data, 0, Size - 1, Target)
                if Target in Data:
                    self.assertEqual(Data[Position], Target)
                    self.assertEqual(Data[RecursivePosition], Target)
                else:
                    self.assertEqual(Position, -1)
                    self.assertEqual(RecursivePosition, -1)

    def test_hash_table_linear_probing(self):
        for Index in range(0, Structures.TableSize):
            Structures.HashTable[Index] = -1
        self.assertEqual(Structures.InsertKey(5), 5)
        self.assertEqual(Structures.InsertKey(16), 6)              # 16 MOD 11 = 5, so the next slot
        self.assertEqual(Structures.FindKey(16), 6)
        self.assertEqual(Structures.FindKey(27), -1)
        for Key in range(100, 109):
            Structures.InsertKey(Key)
        self.assertEqual(Structures.InsertKey(999), -1)            # table full
        self.assertEqual(Structures.FindKey(999), -1)

    def test_classes_and_inheritance(self):
        Car = Structures.Vehicle('Tiger', 100, 20)
        Car.IncreaseSpeed()
        Car.IncreaseSpeed()
        self.assertEqual(Car.GetCurrentSpeed(), 40)
        self.assertEqual(Car.GetHorizontalPosition(), 60)
        Heli = Structures.Helicopter('Lion', 350, 40, 3, 5)
        Heli.IncreaseSpeed()
        Heli.IncreaseSpeed()
        self.assertEqual(Heli.GetVerticalPosition(), 5)            # capped at MaxHeight
        self.assertEqual(Heli.GetCurrentSpeed(), 80)
        self.assertFalse(hasattr(Car, '__CurrentSpeed'))           # name is private

    def test_record_result(self):
        Result = Structures.Evaluate('7', '2')
        self.assertTrue(Result.Done)
        self.assertEqual(Result.Value, 3.5)
        self.assertFalse(Structures.Evaluate('7', '0').Done)
        self.assertFalse(Structures.Evaluate('seven', '2').Done)


if __name__ == '__main__':
    unittest.main()
