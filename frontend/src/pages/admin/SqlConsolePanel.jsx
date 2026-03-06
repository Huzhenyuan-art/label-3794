import { Button, Card, Input, Space, Table, Tag, Typography, message } from 'antd';
import { useMemo, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';

const { TextArea } = Input;
const { Text } = Typography;

function SqlConsolePanel() {
  const [sql, setSql] = useState('SELECT * FROM business_pages LIMIT 20');
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  const columns = useMemo(() => {
    if (!rows.length) {
      return [];
    }
    return Object.keys(rows[0]).map((key) => ({
      title: key,
      dataIndex: key,
      key,
      render: (value) => (typeof value === 'object' ? JSON.stringify(value) : String(value ?? '-')),
    }));
  }, [rows]);

  const runQuery = async () => {
    setLoading(true);
    try {
      const { data } = await http.post('/api/admin/settings/sql/query', { sql });
      setRows(data.data.rows || []);
      message.success(`SQL 执行成功，共 ${data.data.row_count} 行`);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="SQL 查询（仅支持 SELECT/SHOW/DESC）">
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Tag color="orange">仅用于管理员排查数据，请勿执行敏感语句</Tag>
        <TextArea rows={6} value={sql} onChange={(event) => setSql(event.target.value)} />
        <Button type="primary" onClick={runQuery} loading={loading}>
          执行 SQL
        </Button>
        <Text type="secondary">结果行数：{rows.length}</Text>
        <Table
          rowKey={(record, index) => `${index}`}
          columns={columns}
          dataSource={rows}
          loading={loading}
          scroll={{ x: 900 }}
          pagination={{ pageSize: 10 }}
        />
      </Space>
    </Card>
  );
}

export default SqlConsolePanel;
