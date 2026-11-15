#!/usr/bin/env python3

import math
import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from sensor_msgs.msg import Image, CameraInfo
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import PointStamped

from cv_bridge import CvBridge

from ultralytics import YOLO

import tf2_ros
from tf2_ros import TransformException


class SemanticObjectMapper(Node):

    def __init__(self):
        super().__init__('semantic_object_mapper')

        # ---------------------------------------------------------
        # SETTINGS
        # ---------------------------------------------------------

        self.rgb_topic = '/oak/rgb/image_raw'
        self.depth_topic = '/oak/stereo/image_raw'
        self.camera_info_topic = '/oak/rgb/camera_info'

        # RTAB-Map global frame
        self.map_frame = 'map'

        # Minimum YOLO confidence
        self.conf_threshold = 0.50

        # ---------------------------------------------------------
        # YOLO
        # ---------------------------------------------------------

        self.get_logger().info('Loading YOLO...')

        self.model = YOLO('yolo11n.pt')

        self.get_logger().info('YOLO loaded.')

        # ---------------------------------------------------------
        # CAMERA
        # ---------------------------------------------------------

        self.bridge = CvBridge()

        self.rgb_image = None
        self.depth_image = None

        self.fx = None
        self.fy = None
        self.cx = None
        self.cy = None

        self.camera_frame = None

        # ---------------------------------------------------------
        # TF
        # ---------------------------------------------------------

        self.tf_buffer = tf2_ros.Buffer()

        self.tf_listener = tf2_ros.TransformListener(
            self.tf_buffer,
            self
        )

        # ---------------------------------------------------------
        # SUBSCRIBERS
        # ---------------------------------------------------------

        self.create_subscription(
            Image,
            self.rgb_topic,
            self.rgb_callback,
            10
        )

        self.create_subscription(
            Image,
            self.depth_topic,
            self.depth_callback,
            10
        )

        self.create_subscription(
            CameraInfo,
            self.camera_info_topic,
            self.camera_info_callback,
            10
        )

        # ---------------------------------------------------------
        # PUBLISHERS
        # ---------------------------------------------------------

        self.marker_pub = self.create_publisher(
            MarkerArray,
            '/semantic_objects',
            10
        )

        self.debug_pub = self.create_publisher(
            Image,
            '/semantic_detection/image',
            10
        )

        # Run detection
        self.timer = self.create_timer(
            0.15,
            self.detect_objects
        )

        self.marker_id = 0

        self.get_logger().info(
            'Semantic Object Mapper started.'
        )

    # =============================================================
    # CAMERA INFO
    # =============================================================

    def camera_info_callback(self, msg):

        self.fx = msg.k[0]
        self.fy = msg.k[4]

        self.cx = msg.k[2]
        self.cy = msg.k[5]

        self.camera_frame = msg.header.frame_id

    # =============================================================
    # RGB
    # =============================================================

    def rgb_callback(self, msg):

        try:

            self.rgb_image = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

            self.rgb_header = msg.header

        except Exception as e:

            self.get_logger().error(
                f'RGB error: {e}'
            )

    # =============================================================
    # DEPTH
    # =============================================================

    def depth_callback(self, msg):

        try:

            depth = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='passthrough'
            )

            # OAK may publish mm as uint16
            if depth.dtype == np.uint16:

                depth = depth.astype(
                    np.float32
                ) / 1000.0

            else:

                depth = depth.astype(
                    np.float32
                )

            self.depth_image = depth

        except Exception as e:

            self.get_logger().error(
                f'Depth error: {e}'
            )

    # =============================================================
    # GET DEPTH INSIDE YOLO BOX
    # =============================================================

    def get_object_depth(
        self,
        x1,
        y1,
        x2,
        y2
    ):

        if self.depth_image is None:
            return None

        h, w = self.depth_image.shape[:2]

        x1 = max(0, min(x1, w - 1))
        x2 = max(0, min(x2, w - 1))

        y1 = max(0, min(y1, h - 1))
        y2 = max(0, min(y2, h - 1))

        # ---------------------------------------------------------
        # IMPORTANT:
        # Don't use entire bounding box because background pixels
        # can destroy depth estimation.
        #
        # Use center 40% of detection.
        # ---------------------------------------------------------

        width = x2 - x1
        height = y2 - y1

        cx1 = int(
            x1 + width * 0.30
        )

        cx2 = int(
            x2 - width * 0.30
        )

        cy1 = int(
            y1 + height * 0.30
        )

        cy2 = int(
            y2 - height * 0.30
        )

        roi = self.depth_image[
            cy1:cy2,
            cx1:cx2
        ]

        if roi.size == 0:
            return None

        # Remove invalid measurements

        valid = roi[
            np.isfinite(roi)
            & (roi > 0.1)
            & (roi < 20.0)
        ]

        if len(valid) < 10:
            return None

        # Median is much more stable than center pixel

        depth = np.median(valid)

        return float(depth)

    # =============================================================
    # PIXEL -> CAMERA XYZ
    # =============================================================

    def pixel_to_3d(
        self,
        u,
        v,
        depth
    ):

        X = (
            (u - self.cx)
            * depth
            / self.fx
        )

        Y = (
            (v - self.cy)
            * depth
            / self.fy
        )

        Z = depth

        return X, Y, Z

    # =============================================================
    # TRANSFORM CAMERA XYZ -> MAP
    # =============================================================

    def transform_to_map(
        self,
        x,
        y,
        z
    ):

        point = PointStamped()

        point.header.frame_id = self.camera_frame

        point.header.stamp = rclpy.time.Time().to_msg()

        point.point.x = float(x)
        point.point.y = float(y)
        point.point.z = float(z)

        try:

            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                self.camera_frame,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.2)
            )

            # manually apply transform

            t = transform.transform.translation
            q = transform.transform.rotation

            # quaternion rotation matrix

            qx = q.x
            qy = q.y
            qz = q.z
            qw = q.w

            R = np.array([

                [
                    1 - 2 * (qy*qy + qz*qz),
                    2 * (qx*qy - qz*qw),
                    2 * (qx*qz + qy*qw)
                ],

                [
                    2 * (qx*qy + qz*qw),
                    1 - 2 * (qx*qx + qz*qz),
                    2 * (qy*qz - qx*qw)
                ],

                [
                    2 * (qx*qz - qy*qw),
                    2 * (qy*qz + qx*qw),
                    1 - 2 * (qx*qx + qy*qy)
                ]
            ])

            camera_point = np.array([
                x,
                y,
                z
            ])

            translation = np.array([
                t.x,
                t.y,
                t.z
            ])

            map_point = (
                R @ camera_point
            ) + translation

            return map_point

        except TransformException as e:

            self.get_logger().warning(
                f'TF failed: {e}'
            )

            return None

    # =============================================================
    # CREATE 3D BOX
    # =============================================================

    def create_box_marker(
        self,
        object_name,
        xyz,
        box_width,
        box_height,
        box_depth,
        marker_id
    ):

        marker = Marker()

        marker.header.frame_id = self.map_frame
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'semantic_boxes'

        marker.id = marker_id

        marker.type = Marker.CUBE

        marker.action = Marker.ADD

        marker.pose.position.x = float(xyz[0])
        marker.pose.position.y = float(xyz[1])
        marker.pose.position.z = float(xyz[2])

        marker.pose.orientation.w = 1.0

        marker.scale.x = max(
            0.1,
            float(box_width)
        )

        marker.scale.y = max(
            0.1,
            float(box_depth)
        )

        marker.scale.z = max(
            0.1,
            float(box_height)
        )

        # transparent cube

        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 0.30

        marker.lifetime = Duration(
            seconds=0.5
        ).to_msg()

        return marker

    # =============================================================
    # CREATE TEXT LABEL
    # =============================================================

    def create_text_marker(
        self,
        name,
        xyz,
        confidence,
        marker_id
    ):

        marker = Marker()

        marker.header.frame_id = self.map_frame
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'semantic_labels'

        marker.id = marker_id

        marker.type = Marker.TEXT_VIEW_FACING

        marker.action = Marker.ADD

        marker.pose.position.x = float(xyz[0])
        marker.pose.position.y = float(xyz[1])
        marker.pose.position.z = float(xyz[2] + 0.4)

        marker.pose.orientation.w = 1.0

        marker.scale.z = 0.20

        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0

        marker.text = (
            f'{name}\n'
            f'{confidence:.2f}\n'
            f'X:{xyz[0]:.2f} '
            f'Y:{xyz[1]:.2f} '
            f'Z:{xyz[2]:.2f}'
        )

        marker.lifetime = Duration(
            seconds=0.5
        ).to_msg()

        return marker

    # =============================================================
    # YOLO DETECTION
    # =============================================================

    def detect_objects(self):

        if self.rgb_image is None:
            return

        if self.depth_image is None:
            return

        if self.fx is None:
            return

        if self.camera_frame is None:
            return

        frame = self.rgb_image.copy()

        # ---------------------------------------------------------
        # YOLO
        # ---------------------------------------------------------

        results = self.model(
            frame,
            verbose=False,
            conf=self.conf_threshold
        )

        markers = MarkerArray()

        self.marker_id = 0

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                confidence = float(
                    box.conf[0]
                )

                class_id = int(
                    box.cls[0]
                )

                object_name = self.model.names[
                    class_id
                ]

                coords = box.xyxy[0].cpu().numpy()

                x1, y1, x2, y2 = map(
                    int,
                    coords
                )

                # -------------------------------------------------
                # BOX CENTER
                # -------------------------------------------------

                u = int(
                    (x1 + x2) / 2
                )

                v = int(
                    (y1 + y2) / 2
                )

                # -------------------------------------------------
                # GET DEPTH
                # -------------------------------------------------

                depth = self.get_object_depth(
                    x1,
                    y1,
                    x2,
                    y2
                )

                if depth is None:
                    continue

                # -------------------------------------------------
                # PIXEL -> XYZ CAMERA
                # -------------------------------------------------

                X, Y, Z = self.pixel_to_3d(
                    u,
                    v,
                    depth
                )

                # -------------------------------------------------
                # CAMERA -> MAP
                # -------------------------------------------------

                map_xyz = self.transform_to_map(
                    X,
                    Y,
                    Z
                )

                if map_xyz is None:
                    continue

                # -------------------------------------------------
                # ESTIMATE PHYSICAL OBJECT SIZE
                # -------------------------------------------------

                pixel_width = x2 - x1
                pixel_height = y2 - y1

                object_width = (
                    pixel_width
                    * depth
                    / self.fx
                )

                object_height = (
                    pixel_height
                    * depth
                    / self.fy
                )

                # approximate thickness
                object_depth = max(
                    0.15,
                    object_width * 0.5
                )

                # -------------------------------------------------
                # RVIZ BOX
                # -------------------------------------------------

                box_marker = self.create_box_marker(
                    object_name,
                    map_xyz,
                    object_width,
                    object_height,
                    object_depth,
                    self.marker_id
                )

                markers.markers.append(
                    box_marker
                )

                self.marker_id += 1

                # -------------------------------------------------
                # TEXT LABEL
                # -------------------------------------------------

                text_marker = self.create_text_marker(
                    object_name,
                    map_xyz,
                    confidence,
                    self.marker_id
                )

                markers.markers.append(
                    text_marker
                )

                self.marker_id += 1

                # -------------------------------------------------
                # DEBUG IMAGE
                # -------------------------------------------------

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                label = (
                    f'{object_name} '
                    f'{confidence:.2f} '
                    f'{depth:.2f}m'
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                cv2.circle(
                    frame,
                    (u, v),
                    5,
                    (0, 0, 255),
                    -1
                )

                self.get_logger().info(

                    f'{object_name:<12} | '
                    f'camera=({X:.2f}, '
                    f'{Y:.2f}, '
                    f'{Z:.2f}) | '
                    f'map=({map_xyz[0]:.2f}, '
                    f'{map_xyz[1]:.2f}, '
                    f'{map_xyz[2]:.2f})'
                )

        # ---------------------------------------------------------
        # PUBLISH MARKERS
        # ---------------------------------------------------------

        self.marker_pub.publish(
            markers
        )

        # ---------------------------------------------------------
        # PUBLISH DEBUG IMAGE
        # ---------------------------------------------------------

        try:

            debug_msg = self.bridge.cv2_to_imgmsg(
                frame,
                encoding='bgr8'
            )

            debug_msg.header = self.rgb_header

            self.debug_pub.publish(
                debug_msg
            )

        except Exception:
            pass


# =============================================================
# MAIN
# =============================================================

def main(args=None):

    rclpy.init(args=args)

    node = SemanticObjectMapper()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()