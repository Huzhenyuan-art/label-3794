import { ReloadOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, Space, Typography, message } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserAccessToken, saveUserAuth } from '../services/auth';
import http, { extractErrorMessage } from '../services/http';

const { Title, Text } = Typography;

function UserLoginPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [captchaId, setCaptchaId] = useState('');
  const [captchaImage, setCaptchaImage] = useState('');
  const [captchaLoading, setCaptchaLoading] = useState(false);
  const formRef = useRef(null);

  useEffect(() => {
    if (getUserAccessToken()) {
      navigate('/user', { replace: true });
    }
  }, [navigate]);

  const fetchCaptcha = useCallback(async () => {
    setCaptchaLoading(true);
    try {
      const { data } = await http.get('/api/user/captcha');
      setCaptchaId(data.data.captcha_id);
      setCaptchaImage(data.data.image);
      if (formRef.current) {
        formRef.current.setFieldValue('captcha_code', '');
      }
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setCaptchaLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCaptcha();
  }, [fetchCaptcha]);

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const payload = {
        username: values.username,
        password: values.password,
        captcha_id: captchaId,
        captcha_code: values.captcha_code,
      };
      const { data } = await http.post('/api/user/login', payload);
      saveUserAuth(data.data.access_token, data.data.csrf_token);
      message.success('登录成功');
      navigate('/user', { replace: true });
    } catch (error) {
      const errMsg = extractErrorMessage(error);
      fetchCaptcha();
      message.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <Card className="login-card" bordered={false}>
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #4a7dff, #2b5ccc)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 28,
              marginBottom: 12,
              boxShadow: '0 4px 16px rgba(42, 92, 204, 0.3)',
            }}
          >
            <UserOutlined />
          </div>
        </div>
        <Title level={3} style={{ marginBottom: 8, textAlign: 'center' }}>
          用户登录
        </Title>
        <Text type="secondary" style={{ display: 'block', textAlign: 'center' }}>
          登录个人工作台，访问授权的业务页面
        </Text>

        <Form ref={formRef} layout="vertical" onFinish={handleSubmit} style={{ marginTop: 24 }}>
          <Form.Item
            label="账号"
            name="username"
            rules={[{ required: true, message: '请输入账号' }]}
          >
            <Input placeholder="请输入账号" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>

          <Form.Item
            label="验证码"
            name="captcha_code"
            rules={[{ required: true, message: '请输入验证码' }]}
          >
            <Space>
              <Input
                placeholder="请输入验证码"
                maxLength={4}
                style={{ width: 120 }}
              />
              <img
                src={captchaImage}
                alt="验证码"
                onClick={fetchCaptcha}
                title="点击刷新验证码"
                style={{
                  height: 40,
                  borderRadius: 6,
                  cursor: captchaLoading ? 'wait' : 'pointer',
                  border: '1px solid #d9d9d9',
                  opacity: captchaLoading ? 0.6 : 1,
                  verticalAlign: 'middle',
                }}
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchCaptcha}
                loading={captchaLoading}
                title="刷新验证码"
              />
            </Space>
          </Form.Item>

          <Button type="primary" htmlType="submit" block loading={loading}>
            登录工作台
          </Button>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Button type="link" onClick={() => navigate('/')}>
              返回首页
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
}

export default UserLoginPage;
