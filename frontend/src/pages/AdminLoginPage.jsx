import { Button, Card, Form, Input, Typography, message } from 'antd';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAccessToken, saveAuth } from '../services/auth';
import http, { extractErrorMessage } from '../services/http';

const { Title, Text } = Typography;

function AdminLoginPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [requireCaptcha, setRequireCaptcha] = useState(false);
  const [captchaId, setCaptchaId] = useState('');
  const [captchaImage, setCaptchaImage] = useState('');
  const [captchaLoading, setCaptchaLoading] = useState(false);

  useEffect(() => {
    if (getAccessToken()) {
      navigate('/admin', { replace: true });
    }
  }, [navigate]);

  const fetchCaptcha = async () => {
    setCaptchaLoading(true);
    try {
      const { data } = await http.get('/api/auth/admin/captcha');
      setCaptchaId(data.data.captcha_id);
      setCaptchaImage(data.data.image);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setCaptchaLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const payload = { username: values.username, password: values.password };
      if (requireCaptcha) {
        payload.captcha_id = captchaId;
        payload.captcha_code = values.captcha_code;
      }
      const { data } = await http.post('/api/auth/admin/login', payload);
      saveAuth(data.data.access_token, data.data.csrf_token);
      message.success('登录成功');
      navigate('/admin', { replace: true });
    } catch (error) {
      const resp = error?.response?.data || {};
      if (resp.require_captcha) {
        setRequireCaptcha(true);
        fetchCaptcha();
      }
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const handleCaptchaClick = () => {
    if (!captchaLoading) {
      fetchCaptcha();
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

          {requireCaptcha && (
            <Form.Item
              label="验证码"
              name="captcha_code"
              rules={[{ required: true, message: '请输入验证码' }]}
            >
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <Input
                  placeholder="请输入验证码"
                  maxLength={4}
                  style={{ flex: 1 }}
                />
                <img
                  src={captchaImage}
                  alt="验证码"
                  onClick={handleCaptchaClick}
                  title="点击刷新验证码"
                  style={{
                    width: 130,
                    height: 40,
                    borderRadius: 6,
                    cursor: captchaLoading ? 'wait' : 'pointer',
                    border: '1px solid #d9d9d9',
                    opacity: captchaLoading ? 0.6 : 1,
                  }}
                />
              </div>
            </Form.Item>
          )}

          <Button type="primary" htmlType="submit" block loading={loading}>
            登录后台
          </Button>
        </Form>
      </Card>
    </div>
  );
}

export default AdminLoginPage;
