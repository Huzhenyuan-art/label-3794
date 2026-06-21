import { Button, Layout, Menu, Space, Spin, Typography, message } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NotificationCenter from '../components/NotificationCenter';
import { clearAuth, getAccessToken } from '../services/auth';
import http, { extractErrorMessage } from '../services/http';
import BusinessPagesPanel from './admin/BusinessPagesPanel';
import GroupsPanel from './admin/GroupsPanel';
import SettingsPanel from './admin/SettingsPanel';
import TagsPanel from './admin/TagsPanel';
import UsersPanel from './admin/UsersPanel';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: 'pages', label: '业务页面管理' },
  { key: 'groups', label: '分组管理' },
  { key: 'tags', label: '标签管理' },
  { key: 'users', label: '用户管理' },
  { key: 'settings', label: '系统设置 / SQL 查询' },
];

function AdminDashboardPage() {
  const navigate = useNavigate();
  const [selectedKey, setSelectedKey] = useState('pages');
  const [checking, setChecking] = useState(true);
  const [admin, setAdmin] = useState(null);

  const panel = useMemo(() => {
    if (selectedKey === 'groups') {
      return <GroupsPanel />;
    }
    if (selectedKey === 'tags') {
      return <TagsPanel />;
    }
    if (selectedKey === 'users') {
      return <UsersPanel />;
    }
    if (selectedKey === 'settings') {
      return <SettingsPanel />;
    }
    return <BusinessPagesPanel />;
  }, [selectedKey]);

  const checkAuth = async () => {
    if (!getAccessToken()) {
      navigate('/admin/login', { replace: true });
      return;
    }

    try {
      const { data } = await http.get('/api/auth/admin/me');
      setAdmin(data.data);
    } catch (error) {
      clearAuth();
      message.error(extractErrorMessage(error));
      navigate('/admin/login', { replace: true });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const logout = () => {
    clearAuth();
    navigate('/admin/login', { replace: true });
  };

  if (checking) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Layout className="dashboard-layout">
      <Sider width={220} breakpoint="lg" collapsedWidth="0" className="dashboard-sider">
        <div className="dashboard-logo">管理后台</div>
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
            <NotificationCenter />
            <Text className="dashboard-header-text">当前管理员：{admin?.username || '-'}</Text>
            <Button onClick={logout}>退出登录</Button>
          </Space>
        </Header>

        <Content className="dashboard-content">{panel}</Content>
      </Layout>
    </Layout>
  );
}

export default AdminDashboardPage;
