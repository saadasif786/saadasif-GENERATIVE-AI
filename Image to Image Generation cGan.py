# -*- coding: utf-8 -*-
"""ImageToImageTranslation.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1muevANLpfNvRKoAO1drc-vmQqtYZ6Uy0
"""

# Import libraries
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import os
import shutil
import zipfile
from google.colab import drive

import torch
import torch.nn as nn

class DownSample(nn.Module):
    def __init__(self, input_channels, output_channels):
        super(DownSample, self).__init__()
        self.model = nn.Sequential(
            nn.Conv2d(input_channels, output_channels, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2)
        )

    def forward(self, x):
        return self.model(x)

class Upsample(nn.Module):
    def __init__(self, input_channels, output_channels):
        super(Upsample, self).__init__()
        self.model = nn.Sequential(
            nn.ConvTranspose2d(input_channels, output_channels, 4, 2, 1, bias=False),
            nn.InstanceNorm2d(output_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x, skip_input):
        x = self.model(x)
        x = torch.cat((x, skip_input), 1)
        return x

class Generator(nn.Module):
    def __init__(self, in_channels=3, out_channels=3):
        super(Generator, self).__init__()

        self.down1 = DownSample(in_channels, 64)
        self.down2 = DownSample(64, 128)
        self.down3 = DownSample(128, 256)
        self.down4 = DownSample(256, 512)
        self.down5 = DownSample(512, 512)
        self.down6 = DownSample(512, 512)
        self.down7 = DownSample(512, 512)
        self.down8 = DownSample(512, 512)

        self.up1 = Upsample(512, 512)
        self.up2 = Upsample(1024, 512)
        self.up3 = Upsample(1024, 512)
        self.up4 = Upsample(1024, 512)
        self.up5 = Upsample(1024, 256)
        self.up6 = Upsample(512, 128)
        self.up7 = Upsample(256, 64)

        self.final = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.ZeroPad2d((1, 0, 1, 0)),
            nn.Conv2d(128, out_channels, 4, padding=1),
            nn.Tanh()
        )

    def forward(self, x):
        d1 = self.down1(x)
        print("d1:", d1.shape)
        d2 = self.down2(d1)
        print("d2:", d2.shape)
        d3 = self.down3(d2)
        print("d3:", d3.shape)
        d4 = self.down4(d3)
        print("d4:", d4.shape)
        d5 = self.down5(d4)
        print("d5:", d5.shape)
        d6 = self.down6(d5)
        print("d6:", d6.shape)
        d7 = self.down7(d6)
        print("d7:", d7.shape)
        d8 = self.down8(d7)
        print("d8:", d8.shape)

        u1 = self.up1(d8, d7)
        print("u1:", u1.shape)
        u2 = self.up2(u1, d6)
        print("u2:", u2.shape)
        u3 = self.up3(u2, d5)
        print("u3:", u3.shape)
        u4 = self.up4(u3, d4)
        print("u4:", u4.shape)
        u5 = self.up5(u4, d3)
        print("u5:", u5.shape)
        u6 = self.up6(u5, d2)
        print("u6:", u6.shape)
        u7 = self.up7(u6, d1)
        print("u7:", u7.shape)
        u8 = self.final(u7)
        print("u8:", u8.shape)

        return u8

# Example usage:
generator = Generator()
input_tensor = torch.randn(1, 3, 256, 256)
output = generator(input_tensor)
print("Output:", output.shape)

image = torch.rand((1,3,256,256))
out_channels = 3
generator = Generator()
k = generator(image)
print(k.shape)

import torch
import torch.nn as nn

class Discriminator(nn.Module):
    def __init__(self, in_channels=3):
        super(Discriminator, self).__init__()

        self.model = nn.Sequential(
            nn.Conv2d(6, 64, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(64, 128, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(128, 256, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(256, 512, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.ZeroPad2d((1, 0, 1, 0)),
            nn.Conv2d(512, 1, 4, padding=1, bias=False)
        )

    def forward(self, img_A, img_B):
        img_input = torch.cat((img_A, img_B), 1)
        return self.model(img_input)

# Example usage:
discriminator = Discriminator()
img_A = torch.randn(1, 3, 256, 256)
img_B = torch.randn(1, 3, 256, 256)
output = discriminator(img_A, img_B)
print("Output:", output.shape)



loss_comparison = nn.BCEWithLogitsLoss()
L1_loss = nn.L1Loss()

def discriminator_training(inputs,targets,discriminator_opt):
  discriminator_opt.zero_grad()

  output = discriminator(inputs, targets)
  label = torch.ones(size = output.shape, dtype=torch.float, device=device)

  real_loss = loss_comparison(output, label)

  gen_image = generator(inputs).detach()

  fake_output = discriminator(inputs, gen_image)
  fake_label = torch.zeros(size = fake_output.shape, dtype=torch.float, device=device)

  fake_loss = loss_comparison(fake_output, fake_label)

  Total_loss = (real_loss + fake_loss)/2

  Total_loss.backward()

  discriminator_opt.step()

  return Total_loss

def generator_training(inputs, targets, generator_opt, L1_lambda):

  generator_opt.zero_grad()

  generator_image = generator(inputs)

  disc_output = discriminator(inputs, generated_image)
  desired_output = torch.ones(size = disc_output.shape, dtype=torch.float, device=device)

  generator_loss = loss_comparison(disc_output, desird_output) + L1_lambda * torch.abs(generated+_image-targets).sum()

  return generator_loss, generatorimage

L1_lambda = 100
NUM_EPOCHS =100
lr=0.002
betal=0.5
beta2=0.999
device = 'cuda'

from tqdm import tqdm

for epoch in range(NUM_EPOCHS+1):
    print(f"Training epoch {epoch+1}")
    for images,_ in tqdm(dataloader_train):

        inputs = images[:,:,:,256:].to(device)
        targets = images[:,:,:,256:].to(device)

        Disc_Loss = discriminator_training(inputs,targets,discriminator_opt)

        for i in range(2):
             Gen_Loss, generator_image = generator_training(inputs,targets, generator_opt, L1_lambda)

    if (epoch % 5) == 0:
        print_images(inputs,5)
        print_images(generator_image,5)
        print_images(targets,5)