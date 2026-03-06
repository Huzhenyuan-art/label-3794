import {
  AppstoreOutlined,
  ClockCircleOutlined,
  RocketOutlined,
  SearchOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Button,
  Card,
  Col,
  Empty,
  Input,
  Layout,
  Row,
  Select,
  Skeleton,
  Space,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import http, { extractErrorMessage } from '../services/http';
import { formatDate } from '../utils/date';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph, Text } = Typography;

/* 分类随机配色 */
const CATEGORY_COLORS = [
  'blue', 'geekblue', 'cyan', 'purple', 'magenta', 'volcano', 'gold', 'green', 'lime',
];

function colorForCategory(cat) {
  let hash = 0;
  for (let i = 0; i < cat.length; i++) {
    hash = cat.charCodeAt(i) + ((hash << 5) - hash);
  }
  return CATEGORY_COLORS[Math.abs(hash) % CATEGORY_COLORS.length];
}

function HomePage() {
  const navigate = useNavigate();
  const [pages, setPages] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [timeSort, setTimeSort] = useState('newest');

  const pageCountLabel = useMemo(() => `已发布 ${pages.length} 个功能`, [pages.length]);

  const fetchPages = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/public/pages', {
        params: {
          search,
          category,
          time_sort: timeSort,
        },
      });
      setPages(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const { data } = await http.get('/api/public/categories');
      setCategories(data.data || []);
    } catch {
      setCategories([]);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchPages();
  }, [search, category, timeSort]);

  return (
    <Layout className="portal-layout">
      <Header className="portal-header">
        <div className="portal-brand">
          <div className="portal-brand-icon">
            <RocketOutlined />
          </div>
          <div>
            <Title level={3} style={{ margin: 0, color: '#12325d', letterSpacing: '0.5px' }}>
              综合业务主站
            </Title>
            <Text type="secondary" style={{ fontSize: 13 }}>统一发布业务功能页面与数据服务</Text>
          </div>
        </div>
        <Button
          type="primary"
          size="large"
          icon={<SettingOutlined />}
          onClick={() => navigate('/admin/login')}
          className="admin-btn"
        >
          管理后台
        </Button>
      </Header>

      <Content className="portal-content">
        {/* 顶部统计横幅 */}
        <div className="portal-banner">
          <div className="portal-banner-content">
            <Title level={2} style={{ margin: 0, color: '#fff', fontWeight: 700 }}>
              🚀 欢迎使用综合业务主站
            </Title>
            <Paragraph style={{ color: 'rgba(255,255,255,0.85)', marginBottom: 0, fontSize: 15 }}>
              在此浏览和访问所有已发布的业务功能页面，点击卡片即可跳转至对应服务入口。
            </Paragraph>
          </div>
        </div>

        {/* 筛选栏 */}
        <Card className="filter-card" bordered={false}>
          <Row gutter={[16, 12]} align="middle">
            <Col xs={24} sm={24} md={8}>
              <Input.Search
                placeholder="搜索功能名称或简介"
                allowClear
                prefix={<SearchOutlined style={{ color: '#8c9ab5' }} />}
                onSearch={(value) => setSearch(value.trim())}
                onChange={(event) => {
                  if (!event.target.value) {
                    setSearch('');
                  }
                }}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={12} md={6}>
              <Select
                placeholder="按业务分类筛选"
                value={category || undefined}
                allowClear
                onChange={(value) => setCategory(value || '')}
                style={{ width: '100%' }}
                options={categories.map((item) => ({ value: item, label: item }))}
              />
            </Col>
            <Col xs={12} sm={12} md={6}>
              <Select
                value={timeSort}
                onChange={setTimeSort}
                style={{ width: '100%' }}
                options={[
                  { value: 'newest', label: '最新添加' },
                  { value: 'oldest', label: '最早添加' },
                ]}
              />
            </Col>
            <Col xs={24} sm={24} md={4} style={{ textAlign: 'right' }}>
              <Tag color="blue" className="count-tag">{pageCountLabel}</Tag>
            </Col>
          </Row>
        </Card>

        {/* 功能卡片列表 */}
        {loading ? (
          <Row gutter={[20, 20]}>
            {[1, 2, 3, 4, 5, 6].map((item) => (
              <Col xs={24} sm={12} lg={8} key={item}>
                <Card className="feature-card">
                  <Skeleton active paragraph={{ rows: 4 }} />
                </Card>
              </Col>
            ))}
          </Row>
        ) : pages.length ? (
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
                    href={page.route_path}
                    target="_blank"
                    className="card-enter-btn"
                  >
                    访问入口
                  </Button>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Card className="empty-card">
            <Empty description="暂无匹配的业务页面" />
          </Card>
        )}
      </Content>

      <Footer className="portal-footer">
        综合业务主站 · 容器化部署版 © {new Date().getFullYear()}
      </Footer>
    </Layout>
  );
}

export default HomePage;
