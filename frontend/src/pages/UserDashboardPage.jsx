import {
  AppstoreOutlined,
  ClockCircleOutlined,
  KeyOutlined,
  UserOutlined,
  SettingOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  Layout,
  Menu,
  Row,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { clearUserAuth, getUserAccessToken } from '../services/auth';
import http, { extractErrorMessage } from '../services/http';
import { formatDate } from '../utils/date';

const { Header, Sider, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

function colorForCategory(cat) {
  const CATEGORY_COLORS = [
    'blue', 'geekblue', 'cyan', 'purple', 'magenta', 'volcano', 'gold', 'green', 'lime',
  ];
  let hash = 0;
  for (let i = 0; i < cat.length; i++) {
    hash = cat.charCodeAt(i) + ((hash << 5) - hash);
  }
  return CATEGORY_COLORS[Math.abs(hash) % CATEGORY_COLORS.length];
}

const menuItems = [
  { key: 'pages', icon: <AppstoreOutlined />, label: '授权业务页面' },
  { key: 'profile', icon: <UserOutlined />, label: '个人资料' },
  { key: 'password', icon: <KeyOutlined />, label: '修改密码' },
];

function PagesPanel() {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchPages = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/user/authorized-pages');
      setPages(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPages();
  }, []);

  const handlePageEnter = (page) => {
    window.open(page.route_path, '_blank');
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (pages.length === 0) {
    return (
      <Card className="empty-card">
        <Empty
          description={
            <div>
              <Paragraph style={{ marginBottom: 4, fontWeight: 500 }}>暂无授权的业务页面</Paragraph>
              <Text type="secondary">请联系管理员为您开通页面访问权限</Text>
            </div>
          }
        />
      </Card>
    );
  }

  return (
    <>
      <Card
        className="filter-card"
        bordered={false}
        title={`已授权业务页面（${pages.length} 个）`}
      >
        <Text type="secondary">点击卡片进入对应业务页面</Text>
      </Card>
      <Row gutter={[20, 20]}>
        {pages.map((page, index) => (
          <Col xs={24} sm={12} lg={8} key={page.id}>
            <Card
              className="feature-card"
              hoverable
              style={{ animationDelay: `${index * 0.06}s` }}
            >
              <div className="card-header">
                <div className="card-icon-wrapper">
                  <AppstoreOutlined className="card-icon" />
                </div>
                <Tag color={colorForCategory(page.category)} className="card-category-tag">
                  {page.category}
                </Tag>
              </div>

              <Title level={4} className="card-title">
                {page.name}
              </Title>
              <Paragraph className="card-desc" ellipsis={{ rows: 3 }}>
                {page.description}
              </Paragraph>

              <div className="card-meta">
                <Space size={16}>
                  <span className="meta-item">
                    <UserOutlined /> {page.developer}
                  </span>
                  <span className="meta-item">
                    <ClockCircleOutlined /> {formatDate(page.created_at)}
                  </span>
                </Space>
              </div>

              <Button
                type="primary"
                block
                onClick={() => handlePageEnter(page)}
                className="card-enter-btn"
              >
                访问入口
              </Button>
            </Card>
          </Col>
        ))}
      </Row>
    </>
  );
}

function ProfilePanel({ user, onUserUpdate }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      form.setFieldsValue({
        display_name: user.display_name || '',
      });
    }
  }, [user, form]);

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const { data } = await http.put('/api/user/profile', {
        display_name: values.display_name || null,
      });
      onUserUpdate(data.data);
      message.success('个人资料已更新');
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="个人资料" bordered={false} className="filter-card">
      <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ maxWidth: 480 }}>
        <Form.Item label="用户名">
          <Input value={user?.username} disabled />
        </Form.Item>
        <Form.Item name="display_name" label="显示名称">
          <Input placeholder="请输入显示名称" maxLength={64} />
        </Form.Item>
        <Form.Item label="账号状态">
          <Tag color={user?.status === 'active' ? 'green' : 'default'}>
            {user?.status === 'active' ? '正常' : '禁用'}
          </Tag>
        </Form.Item>
        <Form.Item label="注册时间">
          <Input value={formatDate(user?.created_at)} disabled />
        </Form.Item>
        <Form.Item label="上次登录">
          <Input value={formatDate(user?.last_login_at)} disabled />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存修改
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

function PasswordPanel() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      await http.post('/api/user/change-password', {
        old_password: values.old_password,
        new_password: values.new_password,
      });
      form.resetFields();
      message.success('密码修改成功');
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title={
        <Space>
          <SafetyOutlined />
          <span>修改密码</span>
        </Space>
      }
      bordered={false}
      className="filter-card"
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        style={{ maxWidth: 480 }}
      >
        <Form.Item
          label="原密码"
          name="old_password"
          rules={[
            { required: true, message: '请输入原密码' },
            { min: 6, message: '密码长度至少 6 位' },
          ]}
        >
          <Input.Password placeholder="请输入原密码" />
        </Form.Item>
        <Form.Item
          label="新密码"
          name="new_password"
          rules={[
            { required: true, message: '请输入新密码' },
            { min: 6, message: '密码长度至少 6 位' },
          ]}
        >
          <Input.Password placeholder="请输入新密码（至少 6 位）" />
        </Form.Item>
        <Form.Item
          label="确认新密码"
          name="confirm_password"
          dependencies={['new_password']}
          rules={[
            { required: true, message: '请再次输入新密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('new_password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password placeholder="请再次输入新密码" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            确认修改
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

function UserDashboardPage() {
  const navigate = useNavigate();
  const [selectedKey, setSelectedKey] = useState('pages');
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState(null);

  const panel = useMemo(() => {
    if (selectedKey === 'profile') {
      return <ProfilePanel user={user} onUserUpdate={setUser} />;
    }
    if (selectedKey === 'password') {
      return <PasswordPanel />;
    }
    return <PagesPanel />;
  }, [selectedKey, user]);

  const checkAuth = async () => {
    if (!getUserAccessToken()) {
      navigate('/user/login', { replace: true });
      return;
    }

    try {
      const { data } = await http.get('/api/user/me');
      setUser(data.data);
    } catch (error) {
      clearUserAuth();
      message.error(extractErrorMessage(error));
      navigate('/user/login', { replace: true });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const logout = () => {
    clearUserAuth();
    navigate('/user/login', { replace: true });
  };

  if (checking) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" />
      </div>
    );
  }

  const displayName = user?.display_name || user?.username || '用户';

  return (
    <Layout className="dashboard-layout">
      <Sider width={220} breakpoint="lg" collapsedWidth="0" className="dashboard-sider">
        <div className="dashboard-logo">
          <SettingOutlined style={{ marginRight: 6 }} />
          个人工作台
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={(event) => setSelectedKey(event.key)}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <Layout>
        <Header className="dashboard-header">
          <div className="dashboard-header-spacer" />
          <Space size="middle" align="center" className="dashboard-header-actions">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #4a7dff, #2b5ccc)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  fontSize: 14,
                }}
              >
                <UserOutlined />
              </div>
              <Text className="dashboard-header-text">
                {displayName}
              </Text>
            </div>
            <Button onClick={() => navigate('/')}>返回首页</Button>
            <Button onClick={logout}>退出登录</Button>
          </Space>
        </Header>

        <Content className="dashboard-content">{panel}</Content>
      </Layout>
    </Layout>
  );
}

export default UserDashboardPage;
