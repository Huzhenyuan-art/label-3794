import { ReloadOutlined } from '@ant-design/icons';
import { Button, Card, Form, Input, Space, Typography, message } from 'antd';
import { useCallback, useEffect, useRef, useState } from 'react';
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
  const formRef = useRef(null);

  useEffect(() => {
    if (getAccessToken()) {
      navigate('/admin', { replace: true });
    }
  }, [navigate]);

  const fetchCaptcha = useCallback(async () => {
    setCaptchaLoading(true);
    try {
      const { data } = await http.get('/api/auth/admin/captcha');
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
      const errMsg = extractErrorMessage(error);
      if (resp.require_captcha) {
        setRequireCaptcha(true);
        if (!captchaId || errMsg.includes('失效') || errMsg.includes('过期') || errMsg.includes('过期')) {
          fetchCaptcha();
        }
      }
      message.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (requireCaptcha && !captchaId) {
      fetchCaptcha();
    }
  }, [requireCaptcha, captchaId, fetchCaptcha]);

  return (
    <div className="login-page">
      <Card className="login-card" bordered={false}>
        <Title level={3} style={{ marginBottom: 8 }}>
          管理员登录
        </Title>
        <Text type="secondary">登录后可管理业务页面、用户与系统配置</Text>

        <Form ref={formRef} layout="vertical" onFinish={handleSubmit} style={{ marginTop: 24 }}>
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
