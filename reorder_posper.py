#!/usr/bin/env python3
import os
import sys
import shutil

def read_poscar(filepath):
    with open(filepath, 'r') as f:
        # 读取所有非空行并去除首尾空白字符
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 8:
        raise ValueError("POSCAR file is too short.")

    comment = lines[0]
    scaling = lines[1]
    lattice = lines[2:5]
    elements = lines[5].split()
    counts = list(map(int, lines[6].split()))

    current_line = 7  # 索引从0开始，第8行

    # 检查是否存在选择性动力学标志
    selective = False
    selective_line = ""
    if current_line < len(lines) and lines[current_line].lower().startswith(('s', 'selective dynamics')):
        selective = True
        selective_line = lines[current_line]
        current_line += 1

    # 读取坐标类型
    if current_line >= len(lines):
        raise ValueError("POSCAR file missing coordinate type.")
    coord_type = lines[current_line]
    current_line += 1

    total_atoms = sum(counts)

    # 读取原子坐标
    atom_coords = []
    for i in range(total_atoms):
        if current_line >= len(lines):
            break
        line = lines[current_line]
        parts = line.split()
        if selective:
            # 选择性动力学标志：每个坐标后有三个标志
            if len(parts) < 6:
                print(f"Warning: Atom coordinate line {current_line+1} is incomplete or missing selective flags.")
            coord = ' '.join(parts[:3])
        else:
            # 无选择性动力学标志：仅三个坐标
            if len(parts) < 3:
                print(f"Warning: Atom coordinate line {current_line+1} is incomplete.")
            coord = ' '.join(parts[:3])
        atom_coords.append(coord + '\n')  # 保留换行符
        current_line += 1

    print(f"Total atoms expected: {total_atoms}, atoms found: {len(atom_coords)}")

    if len(atom_coords) != total_atoms:
        print("Last few lines read for atom coordinates:")
        for idx in range(max(0, len(atom_coords)-5), len(atom_coords)):
            print(f"Line {idx + 1}: {atom_coords[idx].strip()}")
        raise AssertionError(f"Expected {total_atoms} atom coordinates, but found {len(atom_coords)}.")

    return {
        'comment': comment,
        'scaling': scaling,
        'lattice': lattice,
        'elements': elements,
        'counts': counts,
        'selective': selective,
        'selective_line': selective_line if selective else None,
        'coord_type': coord_type,
        'atom_coords': atom_coords
    }

def write_poscar(filepath, data):
    with open(filepath, 'w') as f:
        f.write("{0}\n".format(data['comment']))
        f.write("{0}\n".format(data['scaling']))
        # 确保每个晶格向量后添加换行符，并格式化数值
        for lattice_line in data['lattice']:
            formatted_line = '  '.join(f"{float(num):.8f}" for num in lattice_line.split())
            f.write("{0}\n".format(formatted_line))
        # 格式化元素和数量行
        f.write('  '.join(data['elements']) + '\n')
        f.write('  '.join(map(str, data['counts'])) + '\n')
        if data['selective']:
            f.write("{0}\n".format(data['selective_line']))
        f.write("{0}\n".format(data['coord_type']))
        # 格式化原子坐标
        for coord in data['atom_coords']:
            parts = coord.strip().split()
            formatted_coord = '  '.join(f"{float(part):.8f}" for part in parts)
            f.write("{0}\n".format(formatted_coord))

def reorder_atoms(data, desired_order=['C', 'H', 'N', 'O']):
    elements = data['elements']
    counts = data['counts']
    atom_coords = data['atom_coords']
    
    # 构建每个原子对应的元素类型列表
    atom_types = []
    for elem, count in zip(elements, counts):
        atom_types.extend([elem] * count)
    
    # 创建 (元素, 坐标) 的元组列表
    atoms = list(zip(atom_types, atom_coords))
    
    # 定义期望的元素顺序
    desired_order = ['C', 'H', 'N', 'O']
    
    # 按照期望的顺序对原子进行排序
    order_dict = {elem: i for i, elem in enumerate(desired_order)}
    sorted_atoms = sorted(atoms, key=lambda x: order_dict.get(x[0], len(desired_order)))
    
    # 提取排序后的元素类型和坐标
    sorted_atom_types, sorted_atom_coords = zip(*sorted_atoms)
    
    # 更新元素和数量
    new_elements = []
    new_counts = []
    current_elem = None
    current_count = 0
    for elem in sorted_atom_types:
        if elem != current_elem:
            if current_elem is not None:
                new_elements.append(current_elem)
                new_counts.append(current_count)
            current_elem = elem
            current_count = 1
        else:
            current_count += 1
    # 添加最后一个元素
    if current_elem is not None:
        new_elements.append(current_elem)
        new_counts.append(current_count)
    
    # 更新数据
    data['elements'] = new_elements
    data['counts'] = new_counts
    data['atom_coords'] = list(sorted_atom_coords)
    
    return data

def main():
    if len(sys.argv) != 2:
        print("Usage: reorder_poscar.py path/to/POSCAR")
        sys.exit(1)
    
    poscar_path = sys.argv[1]
    
    if not os.path.isfile(poscar_path):
        print("Error: {0} does not exist.".format(poscar_path))
        sys.exit(1)
    
    # 备份 POSCAR 文件
    backup_path = poscar_path + ".bak"
    shutil.copyfile(poscar_path, backup_path)
    print("Backup created: {0}".format(backup_path))
    
    try:
        data = read_poscar(poscar_path)
    except AssertionError as e:
        print("AssertionError:", e)
        print("Please check the POSCAR file for consistency.")
        sys.exit(1)
    except ValueError as e:
        print("ValueError:", e)
        print("Please check the POSCAR file for proper formatting.")
        sys.exit(1)
    
    data = reorder_atoms(data, desired_order=['C', 'H', 'N', 'O'])
    write_poscar(poscar_path, data)
    print("Reordered POSCAR: {0}".format(poscar_path))

if __name__ == "__main__":
    main()
