import argparse
import collections
import torch
import data_loader.data_loaders as module_data
import model.loss as module_loss
import model.metric as module_metric
import model.model as module_arch
from parse_config import ConfigParser
from trainer import Trainer
import ipdb
import os
import wandb
import random
import numpy as np

random.seed(0)
np.random.seed(0)
torch.manual_seed(0)
#torch.use_deterministic_algorithms(True), it won't work because we use some algo that are not deterministic

def main(config):
    logger = config.get_logger('train')

    # setup data_loader instances
    config._config['data_loader']['args']['split'] = 'train'
    data_loader = config.initialize('data_loader', module_data)
    config._config['data_loader']['args']['split'] = 'val'
    valid_data_loader = config.initialize('data_loader', module_data)

    # TODO: improve this, safely clone args across config classes
    config._config['arch']['args']['label'] = data_loader.dataset.label
    config._config['arch']['args']['experts_used'] = data_loader.dataset.experts_used
    config._config['arch']['args']['expert_dims'] = data_loader.dataset.expert_dims

    # build model architecture, then print to console
    model = config.initialize('arch', module_arch)
    logger.info(model)

    # get function handles of loss and metrics
    loss = config.initialize(name="loss", module=module_loss)
    metrics = [getattr(module_metric, met) for met in config['metrics']]

    # build optimizer, learning rate scheduler. delete every lines containing lr_scheduler for disabling scheduler
    trainable_params = filter(lambda p: p.requires_grad, model.parameters())
    optimizer = config.initialize('optimizer', torch.optim, trainable_params)

    lr_scheduler = config.initialize('lr_scheduler', torch.optim.lr_scheduler, optimizer)

    trainer = Trainer(model, loss, metrics, optimizer,
                      config=config,
                      data_loader=data_loader,
                      valid_data_loader=valid_data_loader,
                      lr_scheduler=lr_scheduler)

    trainer.train()

    return logger


class TestArg:
    def __init__(self, resume):
        self.resume = resume
        self.device = None
        self.config = None


if __name__ == '__main__':
    args = argparse.ArgumentParser(description='PyTorch Template')
    args.add_argument('config', default=None, type=str,
                      help='config file path (default: None)')
    args.add_argument('-r', '--resume', default=None, type=str,
                      help='path to latest checkpoint (default: None)')
    args.add_argument('-d', '--device', default=None, type=str,
                      help='indices of GPUs to enable (default: all)')

    # custom cli options to modify configuration from default values given in json file.
    #CustomArgs = collections.namedtuple('CustomArgs', 'flags type target')
    #options = [
    #    CustomArgs(['--lr', '--learning_rate'], type=float, target=('optimizer', 'args', 'lr')),
    #    CustomArgs(['--bs', '--batch_size'], type=int, target=('data_loader', 'args', 'batch_size'))
    #]
    config = ConfigParser(args)
    wandb.init(project="condensed movies",config=config,name="FRSSV_-lr=3e-5+val_loss_medR")
    main(config)