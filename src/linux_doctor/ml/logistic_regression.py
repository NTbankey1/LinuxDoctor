"""
Logistic Regression — Phase 4.

Implements multi-class Logistic Regression from scratch using NumPy.

Mathematical Foundation:
    Sigmoid:
        σ(z) = 1 / (1 + exp(-z))

    Softmax (multi-class):
        softmax(z)_k = exp(z_k) / Σ exp(z_j)
                                    j

    Cross-Entropy Loss:
        L(W) = -(1/m) Σ Σ y_ik × log(ŷ_ik)
                       i  k

    Gradient:
        ∂L/∂W = (1/m) × X^T × (Ŷ - Y)   [where Y is one-hot]

    Weight Update (SGD/Mini-batch):
        W := W - η × ∂L/∂W
        b := b - η × mean(Ŷ - Y)

    L2 Regularization:
        L_reg(W) = L(W) + (λ/2) × ||W||²
        Gradient += λ × W
"""

import numpy as np


class LogisticRegression:
    """
    Multi-class Logistic Regression via Softmax + Gradient Descent (from scratch).

    Uses One-vs-Rest softmax with L2 regularization.
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        n_iterations: int = 300,
        lambda_reg: float = 0.01,
        batch_size: int = 32,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the classifier.

        Args:
            learning_rate: η — step size for gradient descent.
            n_iterations: Number of training epochs.
            lambda_reg: λ — L2 regularization strength.
            batch_size: Mini-batch size (set to None for full batch).
            verbose: Print loss every 50 iterations.
        """
        self.lr = learning_rate
        self.n_iter = n_iterations
        self.lambda_reg = lambda_reg
        self.batch_size = batch_size
        self.verbose = verbose

        self.classes_: list[str] = []
        self._W: np.ndarray = np.array([])  # shape: (n_classes, n_features)
        self._b: np.ndarray = np.array([])  # shape: (n_classes,)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _softmax(Z: np.ndarray) -> np.ndarray:
        """
        Numerically stable softmax.

        softmax(z)_k = exp(z_k - max(z)) / Σ exp(z_j - max(z))

        Args:
            Z: Input matrix (m × n_classes).

        Returns:
            Probability matrix (m × n_classes), rows sum to 1.
        """
        # Subtract max for numerical stability (log-sum-exp trick)
        Z_shifted = Z - Z.max(axis=1, keepdims=True)
        exp_Z = np.exp(Z_shifted)
        return exp_Z / exp_Z.sum(axis=1, keepdims=True)

    @staticmethod
    def _one_hot(y_idx: np.ndarray, n_classes: int) -> np.ndarray:
        """
        Convert label indices to one-hot matrix.

        Args:
            y_idx: Integer label array of shape (m,).
            n_classes: Number of classes.

        Returns:
            One-hot matrix (m × n_classes).
        """
        Y = np.zeros((len(y_idx), n_classes), dtype=np.float64)
        Y[np.arange(len(y_idx)), y_idx] = 1.0
        return Y

    def _cross_entropy_loss(self, Y_hat: np.ndarray, Y: np.ndarray) -> float:
        """
        Compute mean cross-entropy loss.

        L = -(1/m) Σ Σ Y_ik × log(Ŷ_ik + ε)
        """
        eps = 1e-12  # clip to avoid log(0)
        return -np.mean(np.sum(Y * np.log(Y_hat + eps), axis=1))

    # -----------------------------------------------------------------------
    # Training
    # -----------------------------------------------------------------------

    def fit(self, X: np.ndarray, y: list[str]) -> "LogisticRegression":
        """
        Train using mini-batch gradient descent with softmax + cross-entropy.

        Args:
            X: Feature matrix (m × n_features).
            y: Class label list of length m.

        Returns:
            self
        """
        m, n_features = X.shape
        self.classes_ = sorted(set(y))
        n_classes = len(self.classes_)
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}
        y_idx = np.array([class_to_idx[label] for label in y])
        Y_one_hot = self._one_hot(y_idx, n_classes)

        # Xavier initialization: keeps variance stable across layers
        scale = np.sqrt(2.0 / (n_features + n_classes))
        self._W = np.random.randn(n_classes, n_features) * scale
        self._b = np.zeros(n_classes, dtype=np.float64)

        bs = self.batch_size if self.batch_size else m

        for epoch in range(self.n_iter):
            # Shuffle for mini-batch
            perm = np.random.permutation(m)
            X_shuf, Y_shuf = X[perm], Y_one_hot[perm]

            for start in range(0, m, bs):
                X_batch = X_shuf[start : start + bs]
                Y_batch = Y_shuf[start : start + bs]
                batch_m = X_batch.shape[0]

                # Forward pass: Z = XW^T + b, Ŷ = softmax(Z)
                Z = X_batch @ self._W.T + self._b        # (batch_m, n_classes)
                Y_hat = self._softmax(Z)                  # (batch_m, n_classes)

                # Gradient of cross-entropy + L2 w.r.t. W
                # ∂L/∂W = (1/m) × (Ŷ - Y)^T × X  +  λ × W
                dZ = (Y_hat - Y_batch) / batch_m          # (batch_m, n_classes)
                dW = dZ.T @ X_batch + self.lambda_reg * self._W  # (n_classes, n_features)
                db = dZ.sum(axis=0)                       # (n_classes,)

                self._W -= self.lr * dW
                self._b -= self.lr * db

            if self.verbose and (epoch + 1) % 50 == 0:
                Z_all = X @ self._W.T + self._b
                Y_hat_all = self._softmax(Z_all)
                loss = self._cross_entropy_loss(Y_hat_all, Y_one_hot)
                print(f"Epoch {epoch+1:4d}/{self.n_iter}  loss={loss:.4f}")

        return self

    # -----------------------------------------------------------------------
    # Inference
    # -----------------------------------------------------------------------

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Compute class probabilities.

        Args:
            X: Feature matrix (m × n_features).

        Returns:
            Probability matrix (m × n_classes).
        """
        Z = X @ self._W.T + self._b
        return self._softmax(Z)

    def predict(self, X: np.ndarray) -> list[str]:
        """
        Predict class labels.

        Args:
            X: Feature matrix (m × n_features).

        Returns:
            List of m predicted class labels.
        """
        probs = self.predict_proba(X)
        best_indices = np.argmax(probs, axis=1)
        return [self.classes_[i] for i in best_indices]
