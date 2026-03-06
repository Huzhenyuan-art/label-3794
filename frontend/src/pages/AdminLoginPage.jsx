import { Button, Card, Form, Input, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAccessToken, saveAuth } from '../services/auth';
import http, { extractErrorMessage } from '../services/http';

const { Title, Text } = Typography;

function AdminLoginPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getAccessToken()) {
      navigate('/admin', { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const { data } = await http.post('/api/auth/admin/login', values);
      saveAuth(data.data.access_token, data.data.csrf_token);
      message.success('登录成功');
      navigate('/admin', { replace: true });
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <Card className="login-card" bordered={false}>
        <Title level={3} style={{ marginBottom: 8 }}>
          管理员登录
        </Title>
        <Text type="secondary">登录后可管理业务页面、用户与系统配置</Text>

        <Form layout="vertical" onFinish={handleSubmit} style={{ marginTop: 24 }}>
          <Form.Item
            label="账号"
            name="username"
            initialValue="admin"
            rules={[{ required: true, message: '请输入管理员账号' }]}
          >
            <Input placeholder="请输入管理员账号" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            initialValue="123456"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Button type="primary" htmlType="submit" block loading={loading}>
            登录后台
          </Button>
        </Form>
      </Card>
    </div>
  );
}

export default AdminLoginPage;
