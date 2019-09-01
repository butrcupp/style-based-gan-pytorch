import argparse
import math

import torch
from torchvision import utils

from model import StyledGenerator


@torch.no_grad()
def get_mean_style(generator, device):
    mean_style = None

    for i in range(10):
        style = generator.mean_style(torch.randn(1024, 512).to(device))

        if mean_style is None:
            mean_style = style

        else:
            mean_style += style

    mean_style /= 10

@torch.no_grad()
def sample(generator, step, mean_style, device):
    image = generator(
        torch.randn(15, 512).to(device),
        step=step,
        alpha=1,
        mean_style=mean_style,
        style_weight=0.7,
    )
    
    return image

@torch.no_grad()
def style_mixing(generator, step, mean_style, device):
    source_code = torch.randn(5, 512).to(device)
    target_code = torch.randn(3, 512).to(device)
    
    shape = 4 * 2 ** step
    alpha = 1

    images = [torch.ones(1, 3, shape, shape).to(device) * -1]

    source_image = generator(
        source_code, step=step, alpha=alpha, mean_style=mean_style, style_weight=0.7
    )
    target_image = generator(
        target_code, step=step, alpha=alpha, mean_style=mean_style, style_weight=0.7
    )

    images.append(source_image)

    for i in range(3):
        image = generator(
            [target_code[i].unsqueeze(0).repeat(5, 1), source_code],
            step=step,
            alpha=alpha,
            mean_style=mean_style,
            style_weight=0.7,
            mixing_range=(0, 1),
        )
        images.append(target_image[i].unsqueeze(0))
        images.append(image)

    images = torch.cat(images, 0)
    
    return images


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=1024, help='size of the image')
    parser.add_argument('path', type=str, help='path to checkpoint file')
    
    args = parser.parse_args()
    
    device = 'cuda'

    generator = StyledGenerator(512).to(device)
    generator.load_state_dict(torch.load(args.path)['g_running'])
    generator.eval()

    mean_style = get_mean_style(generator, device)

    step = int(math.log(args.size, 2)) - 2
    
    img = sample(generator, step, mean_style, device)
    utils.save_image(img, 'sample.png', nrow=5, normalize=True, range=(-1, 1))
    
    for j in range(20):
        img = style_mixing(generator, step, mean_style, device)
        utils.save_image(
            img, f'sample_mixing_{j}.png', nrow=6, normalize=True, range=(-1, 1)
        )