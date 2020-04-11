import inspect
import numpy
import os
import sys
import argparse
import termcolor
from subprocess import Popen, PIPE

# Opening subfolder tools
# Открываем подпапку tools
cmd_subfolder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "tools")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


# Получаем все имена .JSON в папке
def get_json_filenames(path):
    """Get names ending with .json in path and return list of names"""
    names = []
    for file in os.listdir(path):
        if file.endswith(".json"):
            names.append(file)
    return names


# Используя скрипт Google Benchmark compare.py проверяем два файла
def compare_pair(file1, file2, path):
    """Compare two files using Google Benchmark compare.py script and return output string and error, if occurs"""
    path_to_current_folder = os.path.dirname(os.path.realpath(__file__))
    process = Popen(
        ['python', path_to_current_folder + '/tools/compare.py', 'benchmarks',
         path + file1,
         path + file2],
        stdout=PIPE, stderr=PIPE, universal_newlines=True
    )
    (output, err) = process.communicate()
    return output, err


# Создаем массив с левым и правым столбцами дельт
def get_lr_mums(nums):
    """Return an array with left and right columns of deviations"""
    n = len(nums)
    lr_nums = numpy.zeros((int(n / 2), 2))
    j = 0
    for i in range(n):
        if i % 2 == 0:
            lr_nums[j][0] = nums[i]
        else:
            lr_nums[j][1] = nums[i]
            j += 1
    return lr_nums


# Находим числа отклонений вида х.хххх со знаками + или - перед ними и помещаем в массив
def find_nums(output_string):
    """Find numbers (deviations) of a kind +x.xxxx or -x.xxxx and return array of these numbers"""
    nums = []
    temp_string = output_string
    while temp_string:
        if temp_string.startswith('+'):
            temp_string = temp_string[1:]
            try:
                nums.append(float(temp_string[:6]))
            except ValueError:
                pass
        elif temp_string.startswith('-0'):
            temp_string = temp_string[1:]
            try:
                nums.append(-1 * float(temp_string[:6]))
            except ValueError:
                pass
        else:
            temp_string = temp_string[1:]
    lr_nums = get_lr_mums(nums)
    return lr_nums


# Находим отклонение на величину >= 0.05
def find_large_deviation(lr_nums):
    """Find deviation greater than 0.5 and return array of line indexes"""
    n = len(lr_nums)
    indexes = numpy.zeros((n, 2))

    # Находим отклонения большие 0.05 и помещаем номера строк в массив (начало отсчета с первых цифр)
    # Если отклонение положительно, то номер строки положителен, и наоборот
    j = 0
    for i in range(n):
        flag = False
        if lr_nums[i][0] >= 0.05:
            indexes[j][0] = i
            flag = True
        if lr_nums[i][1] >= 0.05:
            indexes[j][1] = i
            flag = True
        if lr_nums[i][0] <= -0.05:
            indexes[j][0] = -1 * i
            flag = True
        if lr_nums[i][1] <= -0.05:
            indexes[j][1] = -1 * i
            flag = True
        if flag:
            j += 1
    indexes = numpy.delete(indexes, slice(j, n), 0)
    return indexes


# Попарная проверка всех файлов в директории
def compare_all(path, names):
    """Compare all files in directory and return list of arrays containing deviations greater than 0.5
    and text for beautified output"""
    lines_in_file = []
    lines_out = []
    err = ''
    are_lines_output_made = False
    for i in range(1, len(names)):
        # Compare files in pairs
        # Сравниваем файлы попарно
        output, err = compare_pair(names[i - 1], names[i], path)

        print('Comparing {0} to {1}'.format(names[i - 1], names[i]))
        # print(output)
        # Make lines for beautified output
        # Создаем строки для красивого вывода
        if not are_lines_output_made:
            lines_out = lines_output(output)
            are_lines_output_made = True

        # Find numbers of deviations in output
        # Находим числа отклонений
        nums_output = find_nums(output)

        # Get array of line numbers of deviations greater than 0.5
        # Получаем массив номеров строк отклонений, больших чем 0,5
        line_number = find_large_deviation(nums_output)

        # Put array into list
        # Кладем массив в список
        lines_in_file.append(line_number)
    return lines_in_file, err, lines_out


# Приводим путь к нормальному виду
def normalize_path(path):
    """Return normalized path string"""
    while path.startswith(' '):
        path = path[1:]
    if not path.endswith('/'):
        path = path + '/'
    return path


# Возвращаем строки с названиями бенчмарков
def lines_output(output):
    """Return array of lines for beatified output"""
    lines = []
    while output:
        if output.startswith('Portf'):
            lines.append(output[:64])  # 43
            output = output[1:]
        elif output.startswith('Match'):
            lines.append(output[:64])  # 61
            output = output[1:]
        elif output.startswith('Misc'):
            lines.append(output[:64])  # 34
            output = output[1:]
        else:
            output = output[1:]
    return lines


# Красивый вывод
def output_message(lines_in_file, lines_out, filename):
    """Print beautified output"""
    worse = termcolor.colored('became worse ', 'red')
    better = termcolor.colored('became better', 'green')
    for i in range(1, len(filename)):
        print("\nComparison of {0} and {1}: ".format(filename[i - 1], filename[i]))
        j = i - 1
        for k in range(len(lines_in_file[j])):
            if lines_in_file[j].item((k, 0)) != 0. and lines_in_file[j].item((k, 1)) != 0.:
                if lines_in_file[j].item((k, 0)) > 0. and lines_in_file[j].item((k, 1)) > 0.:
                    print('    {0}  "Time" {1}    "CPU" {2}'.format(lines_out[k], worse, worse))
                elif lines_in_file[j].item((k, 0)) > 0. and lines_in_file[j].item((k, 1)) < 0.:
                    print('    {0}  "Time" {1}    "CPU" {2}'.format(lines_out[k], worse, better))
                elif lines_in_file[j].item((k, 0)) < 0. and lines_in_file[j].item((k, 1)) > 0.:
                    print('    {0}  "Time" {1}    "CPU" {2}'.format(lines_out[k], better, worse))
                else:
                    print('    {0}  "Time" {1}    "CPU" {2}'.format(lines_out[k], better, better))
            elif lines_in_file[j].item((k, 0)) != 0.:
                if lines_in_file[j].item((k, 0)) > 0.:
                    print('    {0}  "Time" {1}'.format(lines_out[k], worse))
                if lines_in_file[j].item((k, 0)) < 0.:
                    print('    {0}  "Time" {1}'.format(lines_out[k], better))
            else:
                if lines_in_file[j].item((k, 1)) > 0.:
                    print('    {0}                          "CPU" {1}'.format(lines_out[k], worse))
                if lines_in_file[j].item((k, 1)) < 0.:
                    print('    {0}                          "CPU" {1}'.format(lines_out[k], better))


def graphs():
    """Draw graphs for 2 (or more) versions"""
    return 0


def main():
    # Take input from user
    # Ввод директории с бенчмарками
    # (ex: c:/users/trusovii/desktop/results/, c:/users/admin/desktop/MOEX/results/)
    parser = argparse.ArgumentParser(
        description='compare tool for more than 2 benchmark outputs')
    parser.add_argument(
        '--path',
        help="path to benchmark-reports' folder",
        default="c:/users/admin/desktop/MOEX/results/")
    args = parser.parse_args()

    print("In progress\n")

    # print("Enter full pathname of the benchmark-reports' folder")
    path_to_benchmarks = normalize_path(args.path)
    filename = get_json_filenames(path_to_benchmarks)

    # Get list of arrays of line numbers with deviations greater than 0.5
    # Получаем список из массивов номеров строк с отклонениями > 0.5
    lines_in_file, err, lines_out = compare_all(path_to_benchmarks, filename)

    if err:
        print('    err:::', err)
    output_message(lines_in_file, lines_out, filename)

    # TODO: Улучшить вывод программы:
    #      * График для двух (и более) версий, учитывая все значения


if __name__ == '__main__':
    # unittest.main()
    main()
