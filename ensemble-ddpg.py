import logging
from agent import *
from component import *
from utils import *
from model import *
import matplotlib.pyplot as plt

def ddpg_continuous(game, log_dir=None):
    config = Config()
    if log_dir is None:
        log_dir = get_default_log_dir(ddpg_continuous.__name__)
    config.task_fn = lambda: Roboschool(game)
    config.evaluation_env = Roboschool(game, log_dir=log_dir)
    config.actor_network_fn = lambda state_dim, action_dim: DeterministicActorNet(
        action_dim, FCBody(state_dim, (300, 200), gate=F.tanh))
    config.critic_network_fn = lambda state_dim, action_dim: DeterministicCriticNet(
        TwoLayerFCBodyWithAction(state_dim, action_dim, [400, 300], gate=F.tanh))
    config.actor_optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-4)
    config.critic_optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-3)
    config.replay_fn = lambda: Replay(memory_size=1000000, batch_size=64)
    config.discount = 0.99
    config.state_normalizer = RunningStatsNormalizer()
    config.max_steps = 1e6
    config.random_process_fn = lambda action_dim: GaussianProcess(
        action_dim, LinearSchedule(0.3, 0, 1e6))

    config.min_memory_size = 64
    config.target_network_mix = 1e-3
    config.logger = Logger('./log', logger)
    run_episodes(DDPGAgent(config))

def ensemble_ddpg(game, log_dir=None, **kwargs):
    config = Config()
    kwargs.setdefault('tag', ensemble_ddpg.__name__)
    kwargs.setdefault('value_loss_weight', 10.0)
    kwargs.setdefault('num_actors', 5)
    if log_dir is None:
        log_dir = get_default_log_dir(kwargs['tag'])
    config.task_fn = lambda: Roboschool(game)
    config.evaluation_env = Roboschool(game, log_dir=log_dir)
    config.network_fn = lambda state_dim, action_dim: EnsembleDeterministicNet(
        actor_body=FCBody(state_dim, (300, 200), gate=F.tanh),
        critic_body=TwoLayerFCBodyWithAction(state_dim, action_dim, [400, 300], gate=F.tanh),
        action_dim=action_dim, num_actors=kwargs['num_actors']
    )
    config.optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-4)
    config.replay_fn = lambda: Replay(memory_size=1000000, batch_size=64)
    config.discount = 0.99
    config.state_normalizer = RunningStatsNormalizer()
    config.max_steps = 1e6
    config.random_process_fn = lambda action_dim: GaussianProcess(
        action_dim, LinearSchedule(0.3, 0, 1e6))
    config.min_memory_size = 64
    config.target_network_mix = 1e-3
    config.logger = Logger('./log', logger)
    config.merge(kwargs)
    run_episodes(EnsembleDDPGAgent(config))

def multi_runs(game, fn, tag, **kwargs):
    runs = np.arange(0, 5)
    for run in runs:
        log_dir = './log/ensemble-%s/%s/%s-run-%d' % (game, fn.__name__, tag, run)
        fn(game, log_dir, **kwargs)

def plot(**kwargs):
    import matplotlib.pyplot as plt
    figure = kwargs['figure']
    del kwargs['figure']
    plotter = Plotter()
    names = plotter.load_log_dirs(**kwargs)
    data = plotter.load_results(names, episode_window=10)

    plt.figure(figure)
    for i, name in enumerate(names):
        x, y = data[i]
        plt.plot(x, y, color=Plotter.COLORS[i], label=name if i==0 else '')
    plt.legend()
    # plt.ylim([-100, 1400])
    plt.ylim([-200, 1200])
    plt.xlabel('timesteps')
    plt.ylabel('episode return')
    # plt.show()

if __name__ == '__main__':
    mkdir('data')
    mkdir('data/video')
    mkdir('dataset')
    mkdir('log')
    os.system('export OMP_NUM_THREADS=1')
    os.system('export MKL_NUM_THREADS=1')
    torch.set_num_threads(1)
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)

    game = 'RoboschoolHopper-v1'
    # game = 'RoboschoolAnt-v1'

    # ensemble_ddpg(game, num_actors=5, tag='hopper_ensemble_ddpg_run_1')
    # plot(pattern='.*/ensemble_ddpg.*', figure=0)
    # plot(pattern='.*hopper_ensemble_ddpg.*', figure=1)
    # plot(pattern='.*expert-RoboschoolHopper.*', figure=0)
    # plot(pattern='.*expert-RoboschoolReacher.*', figure=0)
    # plt.show()


