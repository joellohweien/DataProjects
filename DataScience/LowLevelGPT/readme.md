# Fine Tune a GPT

This project is a comprehensive guide on fine-tuning a ground up GPT model, inspired by the article "The Art of Hyperparameter Tuning a GPT" on Medium. It demonstrates the use of a Transformer-based neural network to learn and predict text by examining interactions between individual characters.

## Overview

The project includes detailed instructions and code for importing datasets, setting up model architecture, pre-processing data, training, and generating text. It uses Shakespeare's works as an example to train the GPT model.

## Key Features

- Low Level Transformer-based neural network.
- Detailed hyperparameter tuning for optimal performance.
- Sample code for data preprocessing and model training.
- Text generation using the trained model.

## Requirements

- Python 3.x
- PyTorch
- CUDA (for GPU support)

## Installation

```bash
git clone https://github.com/joellohweien/DataProjects.git
cd DataProjects/DataScience/LowLevelGPT/
```

## Usage

1. **Data Import**: The "tinyshakespeare" dataset is used, which can be imported as shown in the notebook.
2. **Hyperparameter Tuning**: The notebook outlines the process of setting and tuning various hyperparameters like learning rate, batch size, number of layers, heads, embedding dimensions, and dropout rates.
3. **Model Training**: Instructions for training the model are included, with details on batch generation, loss estimation, and early stopping.
4. **Text Generation**: Post-training, the model can generate text resembling Shakespeare's style.

## Model Architecture

The architecture details are as follows:
- Multi-head self-attention mechanism.
- Feedforward neural network layers.
- Layer normalization and dropout for regularization.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

