"""Add prompts to code snippets"""


def add_prompts(code, first='>>> ', cont='... '):
    new_code = []
    code_list = code.split('\n')
    new_code.append(first + code_list[0])
    for line in code_list[1:]:
        new_code.append(cont + line)
    return '\n'.join(new_code)

    