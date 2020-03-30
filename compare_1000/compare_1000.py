import inspect
import numpy
import os
import sys
from subprocess import Popen, PIPE

# Открываем подпапку tools
cmd_subfolder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "benchmark")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


# Получаем все имена .JSON в папке
def GetFilesJSON(path):
    names = []

    for file in os.listdir(path):
        if file.endswith(".json"):
            names.append(file)

    return names


# Используя скрипт Google Benchmark compare.py проверяем два файла
def CompareTwo(file1, file2, path):
    path_to_current_folder = os.path.dirname(os.path.realpath(__file__))

    process = Popen(['python', path_to_current_folder + '/benchmark/tools/compare.py', 'benchmarks',
                     path + file1,
                     path + file2],
                    stdout=PIPE, stderr=PIPE, universal_newlines=True)
    (output, err) = process.communicate()

    return output, err


# Находим числа отклонений вида х.хххх со знаками + или - перед ними и помещаем в массив
def FindNums(sOut):
    nums = []
    tempS = sOut
    while tempS != '':
        if tempS[0] == '+':
            tempS = tempS[tempS.find('+') + 1:]
            try:
                nums.append(float(tempS[:6]))
            except ValueError:
                pass
        elif tempS[0] == '-':
            tempS = tempS[tempS.find('-') + 1:]
            try:
                nums.append(-1 * float(tempS[:7]))
            except ValueError:
                pass
        else:
            tempS = tempS[1:]
    return nums


# Находим отклонение на величину >= 0.05
def FindLargeDeviation(nums):
    n = len(nums)
    lrNums = numpy.zeros((n, 2))
    indexes = numpy.zeros((n, 2))

    # Создаем массив с левым и правым столбцами дельт
    j = 0
    for i in range(n):
        if i % 2 == 0:
            lrNums[j][0] = nums[i]
        else:
            lrNums[j][1] = nums[i]
            j += 1

    # находим отклонения большие 0.05 и помечаем номера строк (начало отсчета с первых цифр)
    j = 0
    for i in range(len(lrNums)):
        if lrNums[i][0] >= 0.05:
            indexes[j][0] = i
        if lrNums[i][1] >= 0.05:
            indexes[j][1] = i
        if lrNums[i][0] <= -0.05:
            indexes[j][0] = -1 * i
        if lrNums[i][1] <= -0.05:
            indexes[j][1] = -1 * i
        if abs(indexes[j][0]) == i or abs(indexes[j][1]) == i:
            j += 1

    return indexes


# Попарная проверка всех файлов в директории
def CompareAll(path, names):
    lineNumber = numpy.zeros((56, 2))
    err = ''
    for i in range(1, len(names)):
        output, err = CompareTwo(names[i - 1], names[i], path)  # Сравниваем попарно
        print(names[i - 1] + ' and ' + names[i])
        print(output)
        nums_output = FindNums(output)  # Находим числа отклонений
        lineNumber = FindLargeDeviation(nums_output)  # Среди оных находим большие отклонения

    return lineNumber, err


def main():
    print('Enter full path to the benchmark folder')
    s = input()
    if s.rfind('/') != len(s) - 1:
        s = s + '/'
    pathToBenchmarks = s  # Ввод директории с бенчмарками  (пример: c:/users/trusovii/desktop/results/,
                                                                  # c:/users/admin/desktop/MOEX/results/)

    filename = GetFilesJSON(pathToBenchmarks)  # Получаем имена файлов JSON
    lineNumber, err = CompareAll(pathToBenchmarks, filename)

    print(lineNumber)
    if err != 0:
        print('    err:::', err)


if __name__ == '__main__':
    # unittest.main()
    main()
