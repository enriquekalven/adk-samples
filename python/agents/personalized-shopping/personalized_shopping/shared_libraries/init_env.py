import gym
gym.envs.registration.register(id='WebAgentTextEnv-v0', entry_point='personalized_shopping.shared_libraries.web_agent_site.envs.web_agent_text_env:WebAgentTextEnv')

def init_env(num_products):
    return gym.make('WebAgentTextEnv-v0', observation_mode='text', num_products=num_products)
NUM_PRODUCT_ITEMS = 50000

class EnvRegistry:
    """Container to manage the singleton environment instance."""
    _webshop_env = None

def get_webshop_env():
    """Lazy-load the webshop environment on first access without using global."""
    if EnvRegistry._webshop_env is None:
        EnvRegistry._webshop_env = init_env(NUM_PRODUCT_ITEMS)
        EnvRegistry._webshop_env.reset()
        print(f'Finished initializing WebshopEnv with {NUM_PRODUCT_ITEMS} items.')
    return EnvRegistry._webshop_env