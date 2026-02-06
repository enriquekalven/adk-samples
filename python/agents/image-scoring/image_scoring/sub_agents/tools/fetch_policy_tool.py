import os

def get_policy():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    policy_file_path = os.path.join(script_dir, '../../policy.json')
    with open(policy_file_path) as file:
        policy_text = file.read()
    policy_text_file = {'policy_text': policy_text}
    return policy_text_file