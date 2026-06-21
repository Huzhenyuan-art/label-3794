import {
  AppstoreOutlined,
  ClockCircleOutlined,
  RocketOutlined,
  SearchOutlined,
  SettingOutlined,
  StarFilled,
  StarOutlined,
  TagsOutlined,
  UserOutlined,
  CloseOutlined,
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
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserAccessToken } from '../services/auth';
import http, { extractErrorMessage } from '../services/http';
import { formatDate } from '../utils/date';

const { Header, Content, Footer } = Layout;
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

const FAVORITES_STORAGE_KEY = 'portal_page_favorites';

function HomePage() {
  const navigate = useNavigate();
  const [pages, setPages] = useState([]);
  const [groups, setGroups] = useState([]);
  const [allTags, setAllTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState([]);
  const hasUserLogin = !!getUserAccessToken();

  const [search, setSearch] = useState('');
  const [activeGroupId, setActiveGroupId] = useState('all');
  const [selectedTagIds, setSelectedTagIds] = useState([]);
  const [timeSort, setTimeSort] = useState('newest');

  const pageCountLabel = useMemo(() => `已发布 ${pages.length} 个功能`, [pages.length]);

  const fetchPages = async () => {
    setLoading(true);
    try {
      const params = {
        search,
        time_sort: timeSort,
      };
      if (activeGroupId !== 'all') {
        params.group_id = activeGroupId;
      }
      if (selectedTagIds.length > 0) {
        params.tag_ids = selectedTagIds.join(',');
      }
      const { data } = await http.get('/api/public/pages', { params });
      setPages(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const { data } = await http.get('/api/public/groups');
      setGroups(data.data || []);
    } catch {
      setGroups([]);
    }
  };

  const fetchTags = async () => {
    try {
      const { data } = await http.get('/api/public/tags');
      setAllTags(data.data || []);
    } catch {
      setAllTags([]);
    }
  };

  useEffect(() => {
    fetchGroups();
    fetchTags();
    loadFavorites();
  }, []);

  useEffect(() => {
    fetchPages();
  }, [search, activeGroupId, selectedTagIds, timeSort]);

  const tabItems = useMemo(() => {
    const items = [{ key: 'all', label: '全部' }];
    groups.forEach((g) => {
      items.push({ key: String(g.id), label: g.name });
    });
    return items;
  }, [groups]);

  const loadFavorites = () => {
    try {
      const stored = localStorage.getItem(FAVORITES_STORAGE_KEY);
      if (stored) {
        setFavorites(JSON.parse(stored));
      }
    } catch (error) {
      console.error('加载收藏失败:', error);
      setFavorites([]);
    }
  };

  const saveFavorites = (newFavorites) => {
    try {
      localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(newFavorites));
      setFavorites(newFavorites);
    } catch (error) {
      console.error('保存收藏失败:', error);
    }
  };

  const isFavorite = (pageId) => {
    return favorites.some((f) => f.id === pageId);
  };

  const toggleFavorite = (page, event) => {
    event.stopPropagation();
    if (isFavorite(page.id)) {
      const newFavorites = favorites.filter((f) => f.id !== page.id);
      saveFavorites(newFavorites);
      message.success('已取消收藏');
    } else {
      const favoriteItem = {
        id: page.id,
        name: page.name,
        route_path: page.route_path,
        category: page.category,
        addedAt: Date.now(),
      };
      const newFavorites = [...favorites, favoriteItem];
      saveFavorites(newFavorites);
      message.success('已添加到收藏');
    }
  };

  const removeFavorite = (pageId, event) => {
    event.stopPropagation();
    const newFavorites = favorites.filter((f) => f.id !== pageId);
    saveFavorites(newFavorites);
    message.success('已从收藏移除');
  };

  const recordPageVisit = async (pageId) => {
    try {
      await http.post('/api/public/page-visit', {
        page_id: pageId,
        referrer: document.referrer,
      });
    } catch (error) {
      // 埋点失败不影响用户体验
    }
  };

  const handlePageEnter = (page) => {
    recordPageVisit(page.id);
    window.open(page.route_path, '_blank');
  };

  const toggleTag = (tagId) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((id) => id !== tagId) : [...prev, tagId]
    );
  };

  const clearTagFilter = () => {
    setSelectedTagIds([]);
  };

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
        <Space>
          <Button
            type="default"
            size="large"
            icon={<UserOutlined />}
            onClick={() => navigate(hasUserLogin ? '/user' : '/user/login')}
          >
            {hasUserLogin ? '个人工作台' : '用户登录'}
          </Button>
          <Button
            type="primary"
            size="large"
            icon={<SettingOutlined />}
            onClick={() => navigate('/admin/login')}
            className="admin-btn"
          >
            管理后台
          </Button>
        </Space>
      </Header>

      <Content className="portal-content">
        {favorites.length > 0 && (
          <Card className="favorites-bar" bordered={false}>
            <div className="favorites-bar-header">
              <div className="favorites-bar-title">
                <StarFilled className="favorites-bar-icon" />
                <span>我的收藏</span>
                <Tag color="gold" className="favorites-count">{favorites.length}</Tag>
              </div>
            </div>
            <div className="favorites-list">
              {favorites.map((fav) => (
                <div
                  key={fav.id}
                  className="favorite-item"
                  onClick={() => handlePageEnter(fav)}
                >
                  <div className="favorite-item-icon">
                    <AppstoreOutlined />
                  </div>
                  <div className="favorite-item-info">
                    <div className="favorite-item-name">{fav.name}</div>
                    <div className="favorite-item-category">{fav.category}</div>
                  </div>
                  <Button
                    type="text"
                    size="small"
                    icon={<CloseOutlined />}
                    className="favorite-item-remove"
                    onClick={(e) => removeFavorite(fav.id, e)}
                  />
                </div>
              ))}
            </div>
          </Card>
        )}

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

        <Card className="filter-card" bordered={false} style={{ marginBottom: 16 }}>
          <Tabs
            activeKey={activeGroupId}
            onChange={setActiveGroupId}
            items={tabItems}
            size="large"
            style={{ marginBottom: 8 }}
          />
          {allTags.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <TagsOutlined style={{ color: '#8c9ab5' }} />
              <Text type="secondary" style={{ fontSize: 13 }}>标签筛选：</Text>
              {allTags.map((tag) => (
                <Tag.CheckableTag
                  key={tag.id}
                  checked={selectedTagIds.includes(tag.id)}
                  onChange={() => toggleTag(tag.id)}
                  style={{ marginInlineEnd: 0 }}
                >
                  <span style={{ color: selectedTagIds.includes(tag.id) ? '#fff' : undefined }}>
                    {tag.name}
                  </span>
                </Tag.CheckableTag>
              ))}
              {selectedTagIds.length > 0 && (
                <Button type="link" size="small" onClick={clearTagFilter}>
                  清除筛选
                </Button>
              )}
            </div>
          )}
        </Card>

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
                    <div className="card-header-actions">
                      <Tag color={colorForCategory(page.category)} className="card-category-tag">
                        {page.category}
                      </Tag>
                      <Button
                        type="text"
                        size="small"
                        icon={isFavorite(page.id) ? <StarFilled className="favorite-icon-active" /> : <StarOutlined className="favorite-icon" />}
                        onClick={(e) => toggleFavorite(page, e)}
                        className="favorite-btn"
                      />
                    </div>
                  </div>

                  <Title level={4} className="card-title">
                    {page.name}
                  </Title>
                  <Paragraph className="card-desc" ellipsis={{ rows: 3 }}>
                    {page.description}
                  </Paragraph>

                  {page.tags && page.tags.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Space wrap>
                        {page.tags.map((t) => (
                          <Tag key={t.id} color={t.color}>
                            {t.name}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  )}

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
