"""
Neural Network Models (Agent 11, Module 2)

Provides neural network architectures for NBA game simulation including
feedforward networks, LSTMs, and attention mechanisms.

Integrates with:
- Agent 2 (Monitoring): Track training metrics
- Agent 9 (Performance): Profile network operations
- Agent 10 (Validation): Validate predictions
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import warnings

logger = logging.getLogger(__name__)

# Try importing PyTorch, fall back to sklearn if not available
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import TensorDataset, DataLoader

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning(
        "PyTorch not available. Neural network models will use sklearn fallback."
    )

# Fallback to sklearn MLP
from sklearn.neural_network import MLPRegressor
from sklearn.base import BaseEstimator, RegressorMixin


@dataclass
class TrainingMetrics:
    """Training metrics for neural networks"""

    epoch: int
    train_loss: float
    val_loss: Optional[float] = None
    train_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingHistory:
    """Complete training history"""

    metrics: List[TrainingMetrics] = field(default_factory=list)
    best_epoch: int = 0
    best_val_loss: float = float("inf")
    total_epochs: int = 0

    def add_metrics(self, metrics: TrainingMetrics):
        """Add metrics for an epoch"""
        self.metrics.append(metrics)
        self.total_epochs = metrics.epoch

        # Track best epoch
        if metrics.val_loss is not None and metrics.val_loss < self.best_val_loss:
            self.best_val_loss = metrics.val_loss
            self.best_epoch = metrics.epoch

    def get_summary(self) -> Dict[str, Any]:
        """Get training summary"""
        if not self.metrics:
            return {}

        return {
            "total_epochs": self.total_epochs,
            "best_epoch": self.best_epoch,
            "best_val_loss": self.best_val_loss,
            "final_train_loss": self.metrics[-1].train_loss,
            "final_val_loss": (
                self.metrics[-1].val_loss if self.metrics[-1].val_loss else None
            ),
            "total_training_time": sum(m.train_time for m in self.metrics),
        }


if TORCH_AVAILABLE:

    class FeedforwardNN(nn.Module):
        """
        Feedforward neural network for game outcome prediction.

        Architecture:
        - Multiple hidden layers with configurable sizes
        - BatchNorm and Dropout for regularization
        - ReLU activation
        """

        def __init__(
            self,
            input_size: int,
            hidden_sizes: List[int],
            output_size: int = 1,
            dropout: float = 0.3,
            use_batch_norm: bool = True,
        ):
            """
            Initialize feedforward network.

            Args:
                input_size: Number of input features
                hidden_sizes: List of hidden layer sizes
                output_size: Number of outputs
                dropout: Dropout probability
                use_batch_norm: Whether to use batch normalization
            """
            super().__init__()

            layers = []
            prev_size = input_size

            for hidden_size in hidden_sizes:
                layers.append(nn.Linear(prev_size, hidden_size))
                if use_batch_norm:
                    layers.append(nn.BatchNorm1d(hidden_size))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(dropout))
                prev_size = hidden_size

            # Output layer
            layers.append(nn.Linear(prev_size, output_size))

            self.network = nn.Sequential(*layers)

        def forward(self, x):
            """Forward pass"""
            return self.network(x)

    class LSTMPredictor(nn.Module):
        """
        LSTM network for sequential game prediction.

        Useful for predicting outcomes based on recent game history.
        """

        def __init__(
            self,
            input_size: int,
            hidden_size: int,
            num_layers: int = 2,
            output_size: int = 1,
            dropout: float = 0.3,
        ):
            """
            Initialize LSTM predictor.

            Args:
                input_size: Number of input features per timestep
                hidden_size: LSTM hidden size
                num_layers: Number of LSTM layers
                output_size: Number of outputs
                dropout: Dropout probability
            """
            super().__init__()

            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size,
                hidden_size,
                num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
            )

            self.fc = nn.Linear(hidden_size, output_size)

        def forward(self, x):
            """
            Forward pass.

            Args:
                x: Input tensor of shape (batch, seq_len, input_size)

            Returns:
                Output tensor of shape (batch, output_size)
            """
            # LSTM forward
            lstm_out, _ = self.lstm(x)

            # Take output from last timestep
            last_output = lstm_out[:, -1, :]

            # Fully connected layer
            output = self.fc(last_output)

            return output

    class PyTorchWrapper(BaseEstimator, RegressorMixin):
        """
        Sklearn-compatible wrapper for PyTorch models.

        Provides fit/predict interface compatible with ensemble methods.
        """

        def __init__(
            self,
            model_class: type,
            model_params: Dict[str, Any],
            learning_rate: float = 0.001,
            batch_size: int = 32,
            epochs: int = 100,
            validation_split: float = 0.2,
            early_stopping_patience: int = 10,
            verbose: bool = False,
        ):
            """
            Initialize PyTorch wrapper.

            Args:
                model_class: PyTorch model class
                model_params: Parameters for model initialization
                learning_rate: Learning rate
                batch_size: Batch size for training
                epochs: Maximum number of epochs
                validation_split: Fraction for validation
                early_stopping_patience: Patience for early stopping
                verbose: Whether to print training progress
            """
            self.model_class = model_class
            self.model_params = model_params
            self.learning_rate = learning_rate
            self.batch_size = batch_size
            self.epochs = epochs
            self.validation_split = validation_split
            self.early_stopping_patience = early_stopping_patience
            self.verbose = verbose

            self.model = None
            self.history = TrainingHistory()
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        def fit(self, X, y):
            """
            Fit the model.

            Args:
                X: Training features (numpy array or torch tensor)
                y: Training targets (numpy array or torch tensor)

            Returns:
                self
            """
            # Convert to numpy if needed
            if torch.is_tensor(X):
                X = X.cpu().numpy()
            if torch.is_tensor(y):
                y = y.cpu().numpy()

            # Ensure 2D arrays
            if len(X.shape) == 1:
                X = X.reshape(-1, 1)
            if len(y.shape) == 1:
                y = y.reshape(-1, 1)

            # Split into train/val
            n_samples = len(X)
            n_val = int(n_samples * self.validation_split)
            n_train = n_samples - n_val

            X_train, X_val = X[:n_train], X[n_train:]
            y_train, y_val = y[:n_train], y[n_train:]

            # Create data loaders
            train_dataset = TensorDataset(
                torch.FloatTensor(X_train), torch.FloatTensor(y_train)
            )
            train_loader = DataLoader(
                train_dataset, batch_size=self.batch_size, shuffle=True
            )

            if n_val > 0:
                val_dataset = TensorDataset(
                    torch.FloatTensor(X_val), torch.FloatTensor(y_val)
                )
                val_loader = DataLoader(val_dataset, batch_size=self.batch_size)
            else:
                val_loader = None

            # Initialize model
            self.model = self.model_class(**self.model_params).to(self.device)

            # Loss and optimizer
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

            # Training loop
            best_val_loss = float("inf")
            patience_counter = 0

            for epoch in range(self.epochs):
                start_time = datetime.now()

                # Training phase
                self.model.train()
                train_losses = []

                for batch_X, batch_y in train_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)

                    # Forward pass
                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)

                    # Backward pass
                    loss.backward()
                    optimizer.step()

                    train_losses.append(loss.item())

                train_loss = np.mean(train_losses)

                # Validation phase
                val_loss = None
                if val_loader is not None:
                    self.model.eval()
                    val_losses = []

                    with torch.no_grad():
                        for batch_X, batch_y in val_loader:
                            batch_X = batch_X.to(self.device)
                            batch_y = batch_y.to(self.device)

                            outputs = self.model(batch_X)
                            loss = criterion(outputs, batch_y)
                            val_losses.append(loss.item())

                    val_loss = np.mean(val_losses)

                    # Early stopping
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        patience_counter = 0
                    else:
                        patience_counter += 1

                    if patience_counter >= self.early_stopping_patience:
                        if self.verbose:
                            print(f"Early stopping at epoch {epoch+1}")
                        break

                # Record metrics
                epoch_time = (datetime.now() - start_time).total_seconds()
                metrics = TrainingMetrics(
                    epoch=epoch + 1,
                    train_loss=train_loss,
                    val_loss=val_loss,
                    train_time=epoch_time,
                )
                self.history.add_metrics(metrics)

                if self.verbose and (epoch + 1) % 10 == 0:
                    if val_loss is not None:
                        print(
                            f"Epoch {epoch+1}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}"
                        )
                    else:
                        print(f"Epoch {epoch+1}: train_loss={train_loss:.4f}")

            return self

        def predict(self, X):
            """
            Make predictions.

            Args:
                X: Features (numpy array or torch tensor)

            Returns:
                Predictions (numpy array)
            """
            if self.model is None:
                raise ValueError("Model must be fitted before prediction")

            # Convert to tensor
            if not torch.is_tensor(X):
                X = torch.FloatTensor(X)

            if len(X.shape) == 1:
                X = X.reshape(-1, 1)

            X = X.to(self.device)

            self.model.eval()
            with torch.no_grad():
                predictions = self.model(X)

            return predictions.cpu().numpy().flatten()

        def get_training_history(self) -> TrainingHistory:
            """Get training history"""
            return self.history


# Fallback MLPWrapper for when PyTorch is not available
class MLPWrapper(BaseEstimator, RegressorMixin):
    """
    Sklearn MLP wrapper with consistent interface.

    Used as fallback when PyTorch is not available.
    """

    def __init__(
        self,
        hidden_layer_sizes: Tuple[int, ...] = (100, 50),
        activation: str = "relu",
        learning_rate_init: float = 0.001,
        max_iter: int = 200,
        early_stopping: bool = True,
        validation_fraction: float = 0.2,
        verbose: bool = False,
    ):
        """
        Initialize MLP wrapper.

        Args:
            hidden_layer_sizes: Sizes of hidden layers
            activation: Activation function
            learning_rate_init: Initial learning rate
            max_iter: Maximum iterations
            early_stopping: Whether to use early stopping
            validation_fraction: Fraction for validation
            verbose: Whether to print progress
        """
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation
        self.learning_rate_init = learning_rate_init
        self.max_iter = max_iter
        self.early_stopping = early_stopping
        self.validation_fraction = validation_fraction
        self.verbose = verbose

        self.model = None
        self.history = TrainingHistory()

    def fit(self, X, y):
        """Fit the model"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            self.model = MLPRegressor(
                hidden_layer_sizes=self.hidden_layer_sizes,
                activation=self.activation,
                learning_rate_init=self.learning_rate_init,
                max_iter=self.max_iter,
                early_stopping=self.early_stopping,
                validation_fraction=self.validation_fraction,
                verbose=self.verbose,
                random_state=42,
            )

            self.model.fit(X, y)

            # Record basic metrics
            metrics = TrainingMetrics(
                epoch=self.model.n_iter_, train_loss=self.model.loss_
            )
            self.history.add_metrics(metrics)

        return self

    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")

        return self.model.predict(X)

    def get_training_history(self) -> TrainingHistory:
        """Get training history"""
        return self.history
