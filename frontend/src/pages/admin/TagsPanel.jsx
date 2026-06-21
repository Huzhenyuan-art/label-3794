import {
  Button,
  Card,
  ColorPicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  message,
} from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';
import { formatDate } from '../../utils/date';

const TAG_COLORS = [
  'blue',
  'geekblue',
  'cyan',
  'purple',
  'magenta',
  'volcano',
  'gold',
  'orange',
  'red',
  'green',
  'lime',
];

function TagsPanel() {
  const [loading, setLoading] = useState(false);
  const [tags, setTags] = useState([]);

  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingTag, setEditingTag] = useState(null);

  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const fetchTags = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/admin/tags');
      setTags(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      const payload = {
        name: values.name,
        color: values.color,
      };
      await http.post('/api/admin/tags', payload);
      setCreateOpen(false);
      createForm.resetFields();
      message.success('标签创建成功');
      fetchTags();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const openEdit = (tag) => {
    setEditingTag(tag);
    editForm.setFieldsValue({
      name: tag.name,
      color: tag.color,
      status: tag.status,
    });
    setEditOpen(true);
  };

  const handleUpdate = async () => {
    try {
      const values = await editForm.validateFields();
      const payload = {
        name: values.name,
        color: values.color,
      };
      await http.put(`/api/admin/tags/${editingTag.id}`, payload);
      setEditOpen(false);
      setEditingTag(null);
      message.success('标签更新成功');
      fetchTags();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const toggleStatus = async (tag, enabled) => {
    try {
      await http.patch(`/api/admin/tags/${tag.id}/status`, {
        status: enabled ? 'enabled' : 'disabled',
      });
      message.success('状态已更新');
      fetchTags();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const deleteTag = async (tag) => {
    try {
      await http.delete(`/api/admin/tags/${tag.id}`);
      message.success('标签已删除');
      fetchTags();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const columns = [
    {
      title: '标签名称',
      dataIndex: 'name',
      width: 180,
      render: (value, record) => <Tag color={record.color}>{value}</Tag>,
    },
    {
      title: '颜色',
      dataIndex: 'color',
      width: 120,
      render: (value) => <Tag color={value}>{value}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 150,
      render: (value, record) => (
        <Space>
          <Tag color={value === 'enabled' ? 'green' : 'default'}>
            {value === 'enabled' ? '启用' : '禁用'}
          </Tag>
          <Switch checked={value === 'enabled'} onChange={(checked) => toggleStatus(record, checked)} />
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (value) => formatDate(value),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确认删除该标签？" onConfirm={() => deleteTag(record)} okText="确认" cancelText="取消">
            <Button danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const ColorSelect = ({ value, onChange }) => (
    <Space wrap>
      {TAG_COLORS.map((color) => (
        <Tag
          key={color}
          color={color}
          onClick={() => onChange && onChange(color)}
          style={{
            cursor: 'pointer',
            padding: '4px 12px',
            border: value === color ? '2px solid #1677ff' : '1px solid transparent',
            margin: 4,
          }}
        >
          {color}
        </Tag>
      ))}
    </Space>
  );

  return (
    <Card
      title="标签管理"
      extra={
        <Button type="primary" onClick={() => setCreateOpen(true)}>
          新增标签
        </Button>
      }
    >
      <Table rowKey="id" loading={loading} columns={columns} dataSource={tags} scroll={{ x: 900 }} />

      <Modal
        title="新增标签"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreate}
        okText="提交"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" initialValues={{ color: 'blue' }}>
          <Form.Item name="name" label="标签名称" rules={[{ required: true, message: '请输入标签名称' }]}>
            <Input placeholder="例如：重要、紧急、推荐" maxLength={32} />
          </Form.Item>
          <Form.Item name="color" label="标签颜色" rules={[{ required: true, message: '请选择标签颜色' }]}>
            <ColorSelect />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑标签"
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={handleUpdate}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="标签名称" rules={[{ required: true, message: '请输入标签名称' }]}>
            <Input maxLength={32} />
          </Form.Item>
          <Form.Item name="color" label="标签颜色" rules={[{ required: true, message: '请选择标签颜色' }]}>
            <ColorSelect />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default TagsPanel;
