import { BellOutlined } from '@ant-design/icons';
import { Badge, Button, List, Popover, Space, Tag, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../services/http';

const { Text, Paragraph } = Typography;

const typeMap = {
  upload_failed: { color: 'red', label: '上传失败' },
  account_locked: { color: 'orange', label: '账号锁定' },
  sql_error: { color: 'red', label: 'SQL 报错' },
};

function getTypeInfo(type) {
  return typeMap[type] || { color: 'default', label: type };
}

function NotificationCenter() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const fetchUnreadCount = async () => {
    try {
      const { data } = await http.get('/api/admin/notifications/unread-count');
      setUnreadCount(data.data?.count || 0);
    } catch (error) {
      // 静默失败，避免影响主界面
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/admin/notifications?limit=20');
      setNotifications(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleOpenChange = (newOpen) => {
    setOpen(newOpen);
    if (newOpen) {
      fetchNotifications();
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await http.post(`/api/admin/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, is_read: true } : item
        )
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const handleMarkAllRead = async () => {
    try {
      const { data } = await http.post('/api/admin/notifications/read-all');
      setNotifications((prev) =>
        prev.map((item) => ({ ...item, is_read: true }))
      );
      setUnreadCount(0);
      message.success(data.message || '已全部标记为已读');
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const timer = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(timer);
  }, []);

  const content = (
    <div style={{ width: 360 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 12px',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <Text strong>通知消息</Text>
        <Button type="link" size="small" onClick={handleMarkAllRead} disabled={unreadCount === 0}>
          全部已读
        </Button>
      </div>
      <List
        loading={loading}
        dataSource={notifications}
        locale={{ emptyText: '暂无通知' }}
        renderItem={(item) => {
          const typeInfo = getTypeInfo(item.type);
          return (
            <List.Item
              style={{
                padding: '12px',
                background: item.is_read ? '#fff' : '#f6ffed',
                cursor: 'pointer',
                borderBottom: '1px solid #f0f0f0',
              }}
              onClick={() => !item.is_read && handleMarkRead(item.id)}
            >
              <List.Item.Meta
                title={
                  <Space size={8} style={{ width: '100%' }}>
                    <Tag color={typeInfo.color} style={{ marginRight: 0 }}>
                      {typeInfo.label}
                    </Tag>
                    <Text strong style={{ flex: 1 }} ellipsis>
                      {item.title}
                    </Text>
                  </Space>
                }
                description={
                  <Space direction="vertical" size={4} style={{ width: '100%' }}>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ marginBottom: 0, fontSize: 12, color: '#666' }}
                    >
                      {item.content}
                    </Paragraph>
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {item.created_at}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          );
        }}
      />
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={handleOpenChange}
      placement="bottomRight"
      arrow
    >
      <Badge count={unreadCount} size="small" offset={[-2, 6]}>
        <Button
          type="text"
          className="notification-bell-btn"
          icon={<BellOutlined className="notification-bell-icon" />}
        />
      </Badge>
    </Popover>
  );
}

export default NotificationCenter;
