"""
Linear SVM with Hinge Loss — Phase 5.

Implements multi-class Linear SVM from scratch using NumPy.

Mathematical Foundation:
    Decision Function:
        f(x) = W·x + b

    Hinge Loss (binary, y ∈ {-1, +1}):
        L_hinge = max(0, 1 - y × f(x))

    Regularized Objective (Primal):
        L(W) = λ||W||² + (1/m) Σ max(0, 1 - y_i × (W·x_i + b))

    Subgradient Update:
        IF y_i × (W·x_i + b) < 1:      ← violated margin
            W := W - η × (2λW - y_i × x_i)
            b := b - η × (-y_i)
        ELSE:                            ← correct side
            W := W - η × 2λW

    Multi-class strategy: One-vs-Rest (OvR)
        Train K binary classifiers (K = num classes).
        Predict = argmax of K decision scores.
"""

import numpy as np


class LinearSVM:
    """
    Multi-class Linear SVM via One-vs-Rest + Hinge Loss + SGD (from scratch).

    Each binary classifier separates one class from all others.
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        lambda_reg: float = 0.001,
        n_iterations: int = 500,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the SVM.

        Args:
            learning_rate: η — gradient step size.
            lambda_reg: λ — regularization (controls margin width).
            n_iterations: Training epochs.
            verbose: Print loss every 100 epochs.
        """
        self.lr = learning_rate
        self.lambda_reg = lambda_reg
        self.n_iter = n_iterations
        self.verbose = verbose

        self.classes_: list[str] = []
        self._W: np.ndarray = np.array([])   # (n_classes, n_features)
        self._b: np.ndarray = np.array([])   # (n_classes,)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _binary_labels(y_idx: np.ndarray, target_class: int) -> np.ndarray:
        """
        Convert multi-class labels to binary {-1, +1} for One-vs-Rest.

        Args:
            y_idx: Integer label array.
            target_class: The class to treat as positive (+1).

        Returns:
            Binary label array of same length.
        """
        return np.where(y_idx == target_class, 1.0, -1.0)

    def _hinge_loss(self, X: np.ndarray, y_binary: np.ndarray, w: np.ndarray, b: float) -> float:
        """
        Compute regularized hinge loss for a binary classifier.

        L = λ||w||² + (1/m) Σ max(0, 1 - y_i(w·x_i + b))
        """
        margins = y_binary * (X @ w + b)
        hinge = np.maximum(0.0, 1.0 - margins)
        return self.lambda_reg * np.dot(w, w) + hinge.mean()

    # -----------------------------------------------------------------------
    # Training one binary SVM (One-vs-Rest)
    # -----------------------------------------------------------------------

    def _train_binary(
        self, X: np.ndarray, y_binary: np.ndarray
    ) -> tuple[np.ndarray, float]:
        """
        Train a single binary SVM using SGD with hinge loss subgradient.

        Args:
            X: Feature matrix (m × n_features).
            y_binary: Binary labels {-1, +1} (m,).

        Returns:
            Tuple of (weight_vector, bias).
        """
        m, n = X.shape
        w = np.zeros(n, dtype=np.float64)
        b = 0.0
        indices = np.arange(m)

        for epoch in range(self.n_iter):
            # Learning rate decay: η_t = η / (1 + λ × t)
            eta = self.lr / (1.0 + self.lambda_reg * epoch)
            np.random.shuffle(indices)

            for i in indices:
                x_i = X[i]
                y_i = y_binary[i]
                margin = y_i * (np.dot(w, x_i) + b)

                # Subgradient of hinge loss w.r.t. w and b
                if margin < 1.0:
                    # Violated margin: gradient from both regularizer and hinge
                    w -= eta * (2.0 * self.lambda_reg * w - y_i * x_i)
                    b -= eta * (-y_i)
                else:
                    # Correct side: gradient only from regularizer
                    w -= eta * (2.0 * self.lambda_reg * w)

        return w, b

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def fit(self, X: np.ndarray, y: list[str]) -> "LinearSVM":
        """
        Train K one-vs-rest binary SVMs.

        Args:
            X: Feature matrix (m × n_features).
            y: Class label list of length m.

        Returns:
            self
        """
        self.classes_ = sorted(set(y))
        n_classes = len(self.classes_)
        n_features = X.shape[1]
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}
        y_idx = np.array([class_to_idx[label] for label in y])

        self._W = np.zeros((n_classes, n_features), dtype=np.float64)
        self._b = np.zeros(n_classes, dtype=np.float64)

        for k, cls in enumerate(self.classes_):
            y_binary = self._binary_labels(y_idx, target_class=k)
            w_k, b_k = self._train_binary(X, y_binary)
            self._W[k] = w_k
            self._b[k] = b_k
            if self.verbose:
                loss = self._hinge_loss(X, y_binary, w_k, b_k)
                print(f"Class '{cls}': hinge_loss={loss:.4f}")

        return self

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute raw decision scores for each class.

        score_k(x) = W_k · x + b_k

        Args:
            X: Feature matrix (m × n_features).

        Returns:
            Score matrix (m × n_classes).
        """
        return X @ self._W.T + self._b

    def predict(self, X: np.ndarray) -> list[str]:
        """
        Predict class labels using argmax of decision scores.

        Args:
            X: Feature matrix (m × n_features).

        Returns:
            List of m predicted class labels.
        """
        scores = self.decision_function(X)
        best_indices = np.argmax(scores, axis=1)
        return [self.classes_[i] for i in best_indices]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Approximate probabilities via softmax over decision scores.

        Note: SVM is not a probabilistic model; this is an approximation.

        Args:
            X: Feature matrix (m × n_features).

        Returns:
            Probability matrix (m × n_classes).
        """
        scores = self.decision_function(X)
        # Numerically stable softmax
        scores -= scores.max(axis=1, keepdims=True)
        exp_scores = np.exp(scores)
        return exp_scores / exp_scores.sum(axis=1, keepdims=True)
