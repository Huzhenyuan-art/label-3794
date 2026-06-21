import {
  Card,
  Col,
  DatePicker,
  Row,
  Select,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from 'antd';
import {
  EyeOutlined,
  FireOutlined,
  TeamOutlined,
  FileTextOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import { useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import http, { extractErrorMessage } from '../../services/http';

const { RangePicker } = DatePicker;
const { Title, Text } = Typography;

function StatsPanel() {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [rankingData, setRankingData] = useState([]);
  const [referrerData, setReferrerData] = useState([]);
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ]);
  const [sortBy, setSortBy] = useState('visits');

  const fetchOverview = async () => {
    try {
      const params = {};
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD');
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD');
      const { data } = await http.get('/api/admin/stats/overview', { params });
      setOverview(data.data);
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const fetchTrend = async () => {
    try {
      const params = {};
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD');
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD');
      const { data } = await http.get('/api/admin/stats/trend', { params });
      setTrendData(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const fetchRanking = async () => {
    try {
      const params = { sort_by: sortBy, limit: 20 };
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD');
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD');
      const { data } = await http.get('/api/admin/stats/pages/ranking', { params });
      setRankingData(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const fetchReferrers = async () => {
    try {
      const params = { limit: 15 };
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD');
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD');
      const { data } = await http.get('/api/admin/stats/referrers', { params });
      setReferrerData(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchOverview(),
        fetchTrend(),
        fetchRanking(),
        fetchReferrers(),
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [dateRange, sortBy]);

  const maxVisit = useMemo(() => {
    if (!trendData.length) return 1;
    return Math.max(...trendData.map((d) => d.visits), 1);
  }, [trendData]);

  const maxRankingVisit = useMemo(() => {
    if (!rankingData.length) return 1;
    return Math.max(...rankingData.map((d) => d.visits), 1);
  }, [rankingData]);

  const maxReferrerVisit = useMemo(() => {
    if (!referrerData.length) return 1;
    return Math.max(...referrerData.map((d) => d.visits), 1);
  }, [referrerData]);

  const trendColumns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 120,
      fixed: 'left',
    },
    {
      title: '访问量 (PV)',
      dataIndex: 'visits',
      key: 'visits',
      width: 200,
      render: (value) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: `${Math.max((value / maxVisit) * 100, 2)}%`,
              maxWidth: 120,
              height: 16,
              background: 'linear-gradient(90deg, #1890ff, #69c0ff)',
              borderRadius: 2,
              minWidth: 4,
            }}
          />
          <Text strong>{value}</Text>
        </div>
      ),
    },
    {
      title: '访客数 (UV)',
      dataIndex: 'visitors',
      key: 'visitors',
      width: 200,
      render: (value) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: `${Math.max((value / maxVisit) * 100, 2)}%`,
              maxWidth: 120,
              height: 16,
              background: 'linear-gradient(90deg, #52c41a, #95de64)',
              borderRadius: 2,
              minWidth: 4,
            }}
          />
          <Text type="secondary">{value}</Text>
        </div>
      ),
    },
  ];

  const rankingColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_, __, index) => {
        const rank = index + 1;
        let color = '';
        if (rank === 1) color = '#f5222d';
        else if (rank === 2) color = '#fa8c16';
        else if (rank === 3) color = '#fadb14';
        return (
          <Text strong style={{ color: color || '#666', fontSize: rank <= 3 ? 16 : 14 }}>
            {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
          </Text>
        );
      },
    },
    {
      title: '页面名称',
      dataIndex: 'page_name',
      key: 'page_name',
      render: (value, record) => (
        <Tooltip title={record.route_path}>
          <Text strong>{value}</Text>
        </Tooltip>
      ),
    },
    {
      title: '访问量 (PV)',
      dataIndex: 'visits',
      key: 'visits',
      width: 200,
      sorter: (a, b) => a.visits - b.visits,
      defaultSortOrder: 'descend',
      render: (value) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              width: `${Math.max((value / maxRankingVisit) * 100, 1)}%`,
              maxWidth: 100,
              height: 14,
              background: 'linear-gradient(90deg, #1890ff, #91d5ff)',
              borderRadius: 2,
              minWidth: 3,
            }}
          />
          <Text strong>{value}</Text>
        </div>
      ),
    },
    {
      title: '访客数 (UV)',
      dataIndex: 'visitors',
      key: 'visitors',
      width: 120,
      sorter: (a, b) => a.visitors - b.visitors,
      render: (value) => <Tag color="green">{value}</Tag>,
    },
    {
      title: '最近访问',
      dataIndex: 'last_visit',
      key: 'last_visit',
      width: 160,
      render: (value) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm') : '-'),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Title level={4} style={{ margin: 0 }}>
              <FireOutlined style={{ color: '#fa541c', marginRight: 8 }} />
              访问统计
            </Title>
          </Col>
          <Col>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates)}
              allowClear={false}
              style={{ width: 260 }}
            />
          </Col>
          <Col>
            <Select
              value={sortBy}
              onChange={setSortBy}
              style={{ width: 140 }}
              options={[
                { value: 'visits', label: '按访问量排序' },
                { value: 'visitors', label: '按访客数排序' },
              ]}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总访问量 (PV)"
              value={overview?.total_visits || 0}
              prefix={<EyeOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="独立访客数 (UV)"
              value={overview?.total_visitors || 0}
              prefix={<TeamOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="访问页面数"
              value={overview?.total_pages || 0}
              prefix={<FileTextOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="人均访问次数"
              value={
                overview?.total_visitors
                  ? (overview.total_visits / overview.total_visitors).toFixed(2)
                  : 0
              }
              prefix={<FireOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={{ color: '#fa8c16' }}
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <span>
            <ArrowUpOutlined style={{ color: '#1890ff', marginRight: 8 }} />
            访问趋势
          </span>
        }
      >
        <Table
          rowKey="date"
          dataSource={trendData}
          columns={trendColumns}
          pagination={false}
          loading={loading}
          scroll={{ x: 600, y: 300 }}
          size="small"
        />
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title={
              <span>
                <FireOutlined style={{ color: '#fa541c', marginRight: 8 }} />
                页面热度排行
              </span>
            }
          >
            <Table
              rowKey="page_id"
              dataSource={rankingData}
              columns={rankingColumns}
              pagination={false}
              loading={loading}
              scroll={{ y: 400 }}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title={
              <span>
                <ArrowDownOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                来源 Referrer TOP15
              </span>
            }
          >
            {referrerData.length ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {referrerData.map((item, index) => (
                  <div key={index} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Tooltip title={item.referrer}>
                        <Text
                          style={{
                            fontSize: 12,
                            maxWidth: 180,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'inline-block',
                          }}
                        >
                          {index + 1}. {item.referrer}
                        </Text>
                      </Tooltip>
                      <Tag color="blue" style={{ margin: 0 }}>
                        {item.visits}
                      </Tag>
                    </div>
                    <div
                      style={{
                        width: `${Math.max((item.visits / maxReferrerVisit) * 100, 1)}%`,
                        height: 6,
                        background: 'linear-gradient(90deg, #1890ff, #91d5ff)',
                        borderRadius: 3,
                        minWidth: 4,
                      }}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                暂无来源数据
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default StatsPanel;
