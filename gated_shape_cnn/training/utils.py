import numpy as np
import tensorflow as tf
from scipy.ndimage import distance_transform_edt


def validate_edge_tensor(edge):
    tf.debugging.assert_shapes(
        [(edge, ('b', 'h', 'w', 2))],
        message='edges')
    tf.debugging.assert_type(
        edge,
        tf.float32,
        message='edges')


def validate_label_tensor(label):
    tf.debugging.assert_rank(
       label,
        4,
        message='label')
    # raise value error for consistency with other validations
    try:
        tf.debugging.assert_greater_equal(
            tf.shape(label)[-1],
            2)
    except tf.errors.InvalidArgumentError:
        raise ValueError('must have at least 2 channels in label')
    tf.debugging.assert_type(
        label,
        tf.float32,
        message='label')


def validate_image_tensor(image):
    tf.debugging.assert_shapes(
        [(image, ('b', 'h', 'w', 3))],
        message='image'
    )
    tf.debugging.assert_type(
        image,
        tf.float32,
        message='image')


def _label_to_one_hot_for_boundary(label, n_classes, background_class):
    """
        Converts a segmentation mask (H,W) to (H,W,K) where the last dim is a one
        hot encoding vector
        """
    assert label.ndim == 2, 'label must be of shape (h, w)'
    _mask = []
    for i in range(n_classes):
        if i != background_class:
            _mask.append(label == i)
        else:
            _mask.append(np.zeros_like(label, dtype=np.bool))
    return np.stack(_mask, axis=-1).astype(np.uint8)


def flat_label_to_edge_label(label, n_classes, radius=2, background_class=0):
    """
    Converts a segmentation label (H,W) to a binary edgemap (H,W, 1)
    """
    one_hot = _label_to_one_hot_for_boundary(label, n_classes, background_class)
    one_hot_pad = np.pad(one_hot, ((1, 1), (1, 1), (0, 0)), mode='constant', constant_values=0)
    edgemap = np.zeros(one_hot.shape[:-1])

    for i in range(n_classes):
        dist = distance_transform_edt(one_hot_pad[..., i]) + \
               distance_transform_edt(1.0 - one_hot_pad[..., i])
        dist = dist[1:-1, 1:-1]
        dist[dist > radius] = 0
        edgemap += dist
    edgemap = np.expand_dims(edgemap, axis=-1)
    edgemap = (edgemap > 0).astype(np.uint8)
    return edgemap