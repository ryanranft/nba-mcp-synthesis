"""
Unit Tests for Neural Network Models (Agent 11, Module 2)

Tests feedforward networks, LSTMs, and training utilities.
"""

import pytest
import numpy as np
from datetime import datetime
from mcp_server.simulations.models.neural_networks import (
    TrainingMetrics,
    TrainingHistory,
    MLPWrapper,
    TORCH_AVAILABLE
)

# Conditionally import PyTorch models
if TORCH_AVAILABLE:
    from mcp_server.simulations.models.neural_networks import (
        FeedforwardNN,
        LSTMPredictor,
        PyTorchWrapper
    )
    import torch


class TestTrainingMetrics:
    """Test TrainingMetrics dataclass"""

    def test_training_metrics_creation(self):
        """Test creating training metrics"""
        metrics = TrainingMetrics(
            epoch=10,
            train_loss=0.5,
            val_loss=0.6,
            train_time=2.5
        )
        assert metrics.epoch == 10
        assert metrics.train_loss == 0.5
        assert metrics.val_loss == 0.6
        assert metrics.train_time == 2.5
        assert isinstance(metrics.timestamp, datetime)

    def test_training_metrics_no_val_loss(self):
        """Test metrics without validation loss"""
        metrics = TrainingMetrics(
            epoch=5,
            train_loss=0.8
        )
        assert metrics.epoch == 5
        assert metrics.train_loss == 0.8
        assert metrics.val_loss is None


class TestTrainingHistory:
    """Test TrainingHistory dataclass"""

    def test_training_history_initialization(self):
        """Test initializing training history"""
        history = TrainingHistory()
        assert len(history.metrics) == 0
        assert history.best_epoch == 0
        assert history.best_val_loss == float('inf')
        assert history.total_epochs == 0

    def test_add_metrics(self):
        """Test adding metrics to history"""
        history = TrainingHistory()
        metrics = TrainingMetrics(epoch=1, train_loss=0.5, val_loss=0.6)
        history.add_metrics(metrics)

        assert len(history.metrics) == 1
        assert history.total_epochs == 1

    def test_track_best_epoch(self):
        """Test tracking best epoch"""
        history = TrainingHistory()

        # Add metrics with decreasing validation loss
        history.add_metrics(TrainingMetrics(1, 1.0, 0.9))
        assert history.best_epoch == 1
        assert history.best_val_loss == 0.9

        history.add_metrics(TrainingMetrics(2, 0.8, 0.7))
        assert history.best_epoch == 2
        assert history.best_val_loss == 0.7

        history.add_metrics(TrainingMetrics(3, 0.6, 0.8))  # Val loss increases
        assert history.best_epoch == 2  # Still epoch 2
        assert history.best_val_loss == 0.7

    def test_get_summary_empty(self):
        """Test getting summary from empty history"""
        history = TrainingHistory()
        summary = history.get_summary()
        assert summary == {}

    def test_get_summary(self):
        """Test getting training summary"""
        history = TrainingHistory()
        history.add_metrics(TrainingMetrics(1, 1.0, 0.9, 1.5))
        history.add_metrics(TrainingMetrics(2, 0.8, 0.7, 1.6))
        history.add_metrics(TrainingMetrics(3, 0.6, 0.8, 1.4))

        summary = history.get_summary()
        assert summary['total_epochs'] == 3
        assert summary['best_epoch'] == 2
        assert summary['best_val_loss'] == 0.7
        assert summary['final_train_loss'] == 0.6
        assert summary['final_val_loss'] == 0.8
        assert summary['total_training_time'] == 4.5


class TestMLPWrapper:
    """Test MLPWrapper (sklearn fallback)"""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        return X, y

    def test_mlp_initialization(self):
        """Test initializing MLP wrapper"""
        model = MLPWrapper(hidden_layer_sizes=(50, 25))
        assert model.hidden_layer_sizes == (50, 25)
        assert model.model is None
        assert isinstance(model.history, TrainingHistory)

    def test_mlp_fit(self, sample_data):
        """Test fitting MLP"""
        X, y = sample_data
        model = MLPWrapper(hidden_layer_sizes=(50,), max_iter=50)
        model.fit(X, y)
        assert model.model is not None

    def test_mlp_predict(self, sample_data):
        """Test making predictions with MLP"""
        X, y = sample_data
        model = MLPWrapper(hidden_layer_sizes=(50,), max_iter=50)
        model.fit(X, y)

        predictions = model.predict(X[:10])
        assert len(predictions) == 10

    def test_mlp_predict_unfitted(self):
        """Test prediction fails on unfitted model"""
        X = np.random.randn(10, 5)
        model = MLPWrapper()

        with pytest.raises(ValueError, match="must be fitted"):
            model.predict(X)

    def test_mlp_training_history(self, sample_data):
        """Test getting training history"""
        X, y = sample_data
        model = MLPWrapper(hidden_layer_sizes=(50,), max_iter=50)
        model.fit(X, y)

        history = model.get_training_history()
        assert isinstance(history, TrainingHistory)
        assert len(history.metrics) > 0

    def test_mlp_custom_parameters(self, sample_data):
        """Test MLP with custom parameters"""
        X, y = sample_data
        model = MLPWrapper(
            hidden_layer_sizes=(100, 50, 25),
            activation='tanh',
            learning_rate_init=0.01,
            max_iter=30
        )
        model.fit(X, y)
        predictions = model.predict(X[:10])
        assert len(predictions) == 10


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestPyTorchModels:
    """Test PyTorch neural network models"""

    def test_feedforward_initialization(self):
        """Test initializing feedforward network"""
        model = FeedforwardNN(
            input_size=10,
            hidden_sizes=[50, 25],
            output_size=1
        )
        assert model is not None
        assert isinstance(model, torch.nn.Module)

    def test_feedforward_forward_pass(self):
        """Test forward pass through feedforward network"""
        model = FeedforwardNN(
            input_size=10,
            hidden_sizes=[50, 25],
            output_size=1
        )
        x = torch.randn(5, 10)
        output = model(x)
        assert output.shape == (5, 1)

    def test_feedforward_no_batch_norm(self):
        """Test feedforward without batch normalization"""
        model = FeedforwardNN(
            input_size=10,
            hidden_sizes=[50],
            output_size=1,
            use_batch_norm=False
        )
        x = torch.randn(5, 10)
        output = model(x)
        assert output.shape == (5, 1)

    def test_lstm_initialization(self):
        """Test initializing LSTM predictor"""
        model = LSTMPredictor(
            input_size=10,
            hidden_size=32,
            num_layers=2,
            output_size=1
        )
        assert model is not None
        assert model.hidden_size == 32
        assert model.num_layers == 2

    def test_lstm_forward_pass(self):
        """Test forward pass through LSTM"""
        model = LSTMPredictor(
            input_size=10,
            hidden_size=32,
            num_layers=2,
            output_size=1
        )
        # Input shape: (batch, seq_len, input_size)
        x = torch.randn(5, 8, 10)
        output = model(x)
        assert output.shape == (5, 1)

    def test_lstm_single_layer(self):
        """Test LSTM with single layer"""
        model = LSTMPredictor(
            input_size=10,
            hidden_size=32,
            num_layers=1,
            output_size=1
        )
        x = torch.randn(5, 8, 10)
        output = model(x)
        assert output.shape == (5, 1)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestPyTorchWrapper:
    """Test PyTorchWrapper for sklearn compatibility"""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 2 + X[:, 1] * 3 + np.random.randn(100) * 0.1
        return X, y

    def test_wrapper_initialization(self):
        """Test initializing PyTorch wrapper"""
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [50], 'output_size': 1}
        )
        assert wrapper.model is None
        assert isinstance(wrapper.history, TrainingHistory)

    def test_wrapper_fit(self, sample_data):
        """Test fitting PyTorch model via wrapper"""
        X, y = sample_data
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [50], 'output_size': 1},
            epochs=10,
            verbose=False
        )
        wrapper.fit(X, y)
        assert wrapper.model is not None

    def test_wrapper_predict(self, sample_data):
        """Test making predictions via wrapper"""
        X, y = sample_data
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [50], 'output_size': 1},
            epochs=10,
            verbose=False
        )
        wrapper.fit(X, y)

        predictions = wrapper.predict(X[:10])
        assert len(predictions) == 10

    def test_wrapper_predict_unfitted(self):
        """Test prediction fails on unfitted wrapper"""
        X = np.random.randn(10, 5)
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [50], 'output_size': 1}
        )

        with pytest.raises(ValueError, match="must be fitted"):
            wrapper.predict(X)

    def test_wrapper_training_history(self, sample_data):
        """Test getting training history from wrapper"""
        X, y = sample_data
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [50], 'output_size': 1},
            epochs=10,
            verbose=False
        )
        wrapper.fit(X, y)

        history = wrapper.get_training_history()
        assert isinstance(history, TrainingHistory)
        assert len(history.metrics) > 0

    def test_wrapper_early_stopping(self, sample_data):
        """Test early stopping in wrapper"""
        X, y = sample_data
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [50], 'output_size': 1},
            epochs=100,
            early_stopping_patience=5,
            verbose=False
        )
        wrapper.fit(X, y)

        # Should stop before 100 epochs
        history = wrapper.get_training_history()
        assert history.total_epochs < 100

    def test_wrapper_custom_parameters(self, sample_data):
        """Test wrapper with custom training parameters"""
        X, y = sample_data
        wrapper = PyTorchWrapper(
            model_class=FeedforwardNN,
            model_params={'input_size': 5, 'hidden_sizes': [100, 50], 'output_size': 1},
            learning_rate=0.01,
            batch_size=16,
            epochs=20,
            validation_split=0.3,
            verbose=False
        )
        wrapper.fit(X, y)
        predictions = wrapper.predict(X[:10])
        assert len(predictions) == 10

    def test_wrapper_with_lstm(self, sample_data):
        """Test wrapper with LSTM model"""
        X, y = sample_data

        # Reshape X for LSTM (add sequence dimension)
        X_seq = X.reshape(X.shape[0], 1, X.shape[1])

        wrapper = PyTorchWrapper(
            model_class=LSTMPredictor,
            model_params={'input_size': 5, 'hidden_size': 32, 'num_layers': 2, 'output_size': 1},
            epochs=10,
            verbose=False
        )
        wrapper.fit(X_seq, y)

        predictions = wrapper.predict(X_seq[:10])
        assert len(predictions) == 10
