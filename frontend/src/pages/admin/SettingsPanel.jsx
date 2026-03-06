import { Button, Card, Col, Form, Input, InputNumber, Row, Space, message } from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';

const { TextArea } = Input;

function splitToList(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function SettingsPanel() {
  const [loading, setLoading] = useState(false);
  const [systemForm] = Form.useForm();
  const [dbForm] = Form.useForm();
  const [pwdForm] = Form.useForm();
  const [sqlValue, setSqlValue] = useState('');
  const [sqlLoading, setSqlLoading] = useState(false);
  const [sqlResult, setSqlResult] = useState('');

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/admin/settings/overview');
      const system = data.data.system_setting;
      const db = data.data.db_config;

      systemForm.setFieldsValue({
        upload_size_limit_mb: system.upload_size_limit_mb,
        allowed_extensions: (system.allowed_extensions || []).join(','),
        allowed_mime_types: (system.allowed_mime_types || []).join(','),
      });

      dbForm.setFieldsValue({
        host: db.host,
        port: db.port,
        username: db.username,
        database_name: db.database_name,
        table_prefix_rule: db.table_prefix_rule,
      });
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const submitSystem = async () => {
    try {
      const values = await systemForm.validateFields();
      await http.put('/api/admin/settings/system', {
        upload_size_limit_mb: values.upload_size_limit_mb,
        allowed_extensions: splitToList(values.allowed_extensions),
        allowed_mime_types: splitToList(values.allowed_mime_types),
      });
      message.success('系统配置更新成功');
      fetchOverview();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const submitDb = async () => {
    try {
      const values = await dbForm.validateFields();
      await http.put('/api/admin/settings/db-config', values);
      message.success('数据库配置更新成功');
      dbForm.setFieldValue('password', '');
      fetchOverview();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const submitPwd = async () => {
    try {
      const values = await pwdForm.validateFields();
      await http.post('/api/admin/settings/password', values);
      message.success('管理员密码修改成功');
      pwdForm.resetFields();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const executeSql = async () => {
    if (!sqlValue.trim()) {
      message.warning('请输入 SQL 语句');
      return;
    }
    setSqlLoading(true);
    setSqlResult('');
    try {
      const { data } = await http.post('/api/admin/settings/sql/query', { sql: sqlValue });
      const rows = data.data?.rows || [];
      setSqlResult(`执行成功，共 ${rows.length} 行结果。\n${JSON.stringify(rows, null, 2)}`);
      message.success(`SQL 执行成功，共 ${rows.length} 行`);
    } catch (error) {
      setSqlResult(`执行失败: ${extractErrorMessage(error)}`);
      message.error(extractErrorMessage(error));
    } finally {
      setSqlLoading(false);
    }
  };

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card title="系统设置" loading={loading}>
        <Form form={systemForm} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="上传大小限制（MB）"
                name="upload_size_limit_mb"
                rules={[{ required: true, message: '请输入上传大小限制' }]}
              >
                <InputNumber min={1} max={500} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={16}>
              <Form.Item
                label="允许扩展名（逗号分隔）"
                name="allowed_extensions"
                rules={[{ required: true, message: '请输入允许扩展名' }]}
              >
                <Input placeholder="html,css,js,zip,png,jpg" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            label="允许 MIME 类型（逗号分隔）"
            name="allowed_mime_types"
            rules={[{ required: true, message: '请输入允许 MIME 类型' }]}
          >
            <Input placeholder="text/html,text/css,application/javascript,application/zip" />
          </Form.Item>
          <Button type="primary" onClick={submitSystem}>
            保存系统设置
          </Button>
        </Form>
      </Card>

      <Card title="数据库连接配置" loading={loading}>
        <Form form={dbForm} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="主机" name="host" rules={[{ required: true, message: '请输入主机' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="端口" name="port" rules={[{ required: true, message: '请输入端口' }]}
              >
                <InputNumber min={1} max={65535} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                label="数据库账号"
                name="username"
                rules={[{ required: true, message: '请输入数据库账号' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="数据库密码"
                name="password"
                rules={[{ required: true, message: '请输入数据库密码' }]}
              >
                <Input.Password placeholder="每次提交需输入密码" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                label="数据库名"
                name="database_name"
                rules={[{ required: true, message: '请输入数据库名' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                label="表前缀规则"
                name="table_prefix_rule"
                rules={[{ required: true, message: '请输入表前缀规则' }]}
                extra="支持占位符: {page_id}, {timestamp}, {rand}"
              >
                <Input placeholder="page_{page_id}_" />
              </Form.Item>
            </Col>
          </Row>

          <Button type="primary" onClick={submitDb}>
            保存数据库配置
          </Button>
        </Form>
      </Card>

      <Card title="SQL 查询 / 执行">
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <TextArea
            rows={5}
            value={sqlValue}
            onChange={(e) => setSqlValue(e.target.value)}
            placeholder="输入 SQL 语句（当前仅支持 SELECT / SHOW / DESC 查询）"
          />
          <Button type="primary" onClick={executeSql} loading={sqlLoading}>
            执行 SQL
          </Button>
          {sqlResult && (
            <pre style={{
              background: '#f5f7fa',
              padding: 16,
              borderRadius: 8,
              maxHeight: 300,
              overflow: 'auto',
              fontSize: 13,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}>
              {sqlResult}
            </pre>
          )}
        </Space>
      </Card>

      <Card title="修改管理员密码">
        <Form form={pwdForm} layout="inline">
          <Form.Item
            name="old_password"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password placeholder="旧密码" />
          </Form.Item>
          <Form.Item
            name="new_password"
            rules={[{ required: true, message: '请输入新密码' }]}
          >
            <Input.Password placeholder="新密码" />
          </Form.Item>
          <Button type="primary" onClick={submitPwd}>
            更新密码
          </Button>
        </Form>
      </Card>
    </Space>
  );
}

export default SettingsPanel;
