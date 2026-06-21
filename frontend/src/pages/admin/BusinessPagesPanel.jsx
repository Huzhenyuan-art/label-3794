import {
  Button,
  Card,
  Checkbox,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  Upload,
  message,
} from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';
import { formatDate } from '../../utils/date';

const { TextArea } = Input;

function BusinessPagesPanel() {
  const [loading, setLoading] = useState(false);
  const [pages, setPages] = useState([]);
  const [groups, setGroups] = useState([]);
  const [tags, setTags] = useState([]);

  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [bindOpen, setBindOpen] = useState(false);
  const [editingPage, setEditingPage] = useState(null);
  const [bindingPage, setBindingPage] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);

  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [bindForm] = Form.useForm();

  const fetchPages = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/admin/pages');
      setPages(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const { data } = await http.get('/api/admin/groups', { params: { status: 'enabled' } });
      setGroups(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const fetchTags = async () => {
    try {
      const { data } = await http.get('/api/admin/tags', { params: { status: 'enabled' } });
      setTags(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  useEffect(() => {
    fetchPages();
    fetchGroups();
    fetchTags();
  }, []);

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      if (!uploadFile) {
        message.warning('请先上传页面文件');
        return;
      }

      const formData = new FormData();
      formData.append('name', values.name);
      formData.append('description', values.description);
      formData.append('category', values.category);
      formData.append('developer', values.developer);
      formData.append('main_page', values.main_page);
      formData.append('file', uploadFile);

      // 如果用户填写了 SQL 语句，一并提交
      if (values.init_sql && values.init_sql.trim()) {
        formData.append('init_sql', values.init_sql.trim());
      }

      const { data } = await http.post('/api/admin/pages', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setCreateOpen(false);
      createForm.resetFields();
      setUploadFile(null);
      message.success('业务页面创建成功');

      Modal.info({
        title: '页面 API Token（请妥善保存）',
        content: data.data.page_api_token,
        okText: '我已保存',
      });

      fetchPages();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const openEdit = (page) => {
    setEditingPage(page);
    editForm.setFieldsValue({
      name: page.name,
      description: page.description,
      category: page.category,
      developer: page.developer,
      status: page.status,
    });
    setEditOpen(true);
  };

  const handleUpdate = async () => {
    try {
      const values = await editForm.validateFields();
      await http.put(`/api/admin/pages/${editingPage.id}`, values);
      setEditOpen(false);
      setEditingPage(null);
      message.success('页面信息已更新');
      fetchPages();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const openBind = (page) => {
    setBindingPage(page);
    bindForm.setFieldsValue({
      group_ids: page.groups ? page.groups.map((g) => g.id) : [],
      tag_ids: page.tags ? page.tags.map((t) => t.id) : [],
    });
    setBindOpen(true);
  };

  const handleBind = async () => {
    try {
      const values = await bindForm.validateFields();
      await http.put(`/api/admin/pages/${bindingPage.id}/groups-tags`, {
        group_ids: values.group_ids || [],
        tag_ids: values.tag_ids || [],
      });
      setBindOpen(false);
      setBindingPage(null);
      message.success('分组与标签绑定成功');
      fetchPages();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const toggleStatus = async (page, enabled) => {
    try {
      await http.patch(`/api/admin/pages/${page.id}/status`, {
        status: enabled ? 'enabled' : 'disabled',
      });
      message.success('状态已更新');
      fetchPages();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const deletePage = async (page) => {
    try {
      await http.delete(`/api/admin/pages/${page.id}`);
      message.success('页面已删除');
      fetchPages();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const resetToken = async (page) => {
    try {
      const { data } = await http.post(`/api/admin/pages/${page.id}/reset-token`);
      Modal.info({
        title: `页面 ${page.name} 的新 Token`,
        content: data.data.page_api_token,
        okText: '我已保存',
      });
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const columns = [
    {
      title: '功能名称',
      dataIndex: 'name',
      width: 180,
    },
    {
      title: '简介',
      dataIndex: 'description',
      ellipsis: true,
    },
    {
      title: '分类',
      dataIndex: 'category',
      width: 120,
      render: (value) => <Tag color="blue">{value}</Tag>,
    },
    {
      title: '所属分组',
      dataIndex: 'groups',
      width: 180,
      render: (value) =>
        value && value.length ? (
          <Space wrap>
            {value.map((g) => (
              <Tag key={g.id} color="geekblue">
                {g.name}
              </Tag>
            ))}
          </Space>
        ) : (
          '-'
        ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      width: 200,
      render: (value) =>
        value && value.length ? (
          <Space wrap>
            {value.map((t) => (
              <Tag key={t.id} color={t.color}>
                {t.name}
              </Tag>
            ))}
          </Space>
        ) : (
          '-'
        ),
    },
    {
      title: '访问路由',
      dataIndex: 'route_path',
      width: 200,
      render: (value) => (
        <a href={value} target="_blank" rel="noreferrer">
          {value}
        </a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (_, record) => (
        <Switch checked={record.status === 'enabled'} onChange={(checked) => toggleStatus(record, checked)} />
      ),
    },
    {
      title: '添加时间',
      dataIndex: 'created_at',
      width: 160,
      render: (value) => formatDate(value),
    },
    {
      title: '操作',
      key: 'actions',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Button size="small" onClick={() => openBind(record)}>
            绑定分组/标签
          </Button>
          <Button size="small" onClick={() => resetToken(record)}>
            重置Token
          </Button>
          <Popconfirm title="确认删除该页面？" onConfirm={() => deletePage(record)} okText="确认" cancelText="取消">
            <Button danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="业务页面管理"
      extra={
        <Button type="primary" onClick={() => setCreateOpen(true)}>
          新增页面
        </Button>
      }
    >
      <Table rowKey="id" loading={loading} columns={columns} dataSource={pages} scroll={{ x: 1600 }} />

      <Modal
        title="新增业务页面"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreate}
        okText="提交"
        cancelText="取消"
        width={640}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" initialValues={{ main_page: 'index.html' }}>
          <Form.Item name="name" label="功能名称" rules={[{ required: true, message: '请输入功能名称' }]}>
            <Input placeholder="例如：设备巡检平台" />
          </Form.Item>
          <Form.Item
            name="description"
            label="功能简介"
            rules={[{ required: true, message: '请输入功能简介' }]}
          >
            <TextArea rows={3} placeholder="请输入业务说明" />
          </Form.Item>
          <Form.Item name="category" label="业务分类" rules={[{ required: true, message: '请输入分类' }]}>
            <Input placeholder="例如：运维、财务、生产" />
          </Form.Item>
          <Form.Item name="developer" label="开发者" rules={[{ required: true, message: '请输入开发者' }]}>
            <Input placeholder="例如：张三" />
          </Form.Item>
          <Form.Item
            name="main_page"
            label="主页面名称"
            rules={[{ required: true, message: '请输入主页面文件名' }]}
            extra="示例：index.html 或 web/index.html"
          >
            <Input placeholder="index.html" />
          </Form.Item>
          <Form.Item label="页面文件（ZIP 或单文件）" required>
            <Upload
              maxCount={1}
              beforeUpload={() => false}
              onRemove={() => setUploadFile(null)}
              onChange={(event) => {
                const file = event.fileList?.[0]?.originFileObj || null;
                setUploadFile(file);
              }}
            >
              <Button>选择文件</Button>
            </Upload>
          </Form.Item>
          <Form.Item
            name="init_sql"
            label="初始化 SQL（可选）"
            extra="可在此输入建表或初始数据 SQL，页面创建时将自动执行。仅支持单条 SQL 语句。"
          >
            <TextArea rows={4} placeholder="例如：CREATE TABLE my_data (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100));" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑业务页面"
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={handleUpdate}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="功能名称" rules={[{ required: true, message: '请输入功能名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item
            name="description"
            label="功能简介"
            rules={[{ required: true, message: '请输入功能简介' }]}
          >
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="category" label="业务分类" rules={[{ required: true, message: '请输入业务分类' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="developer" label="开发者" rules={[{ required: true, message: '请输入开发者' }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={bindingPage ? `绑定分组与标签 - ${bindingPage.name}` : '绑定分组与标签'}
        open={bindOpen}
        onCancel={() => setBindOpen(false)}
        onOk={handleBind}
        okText="保存"
        cancelText="取消"
        width={560}
        destroyOnClose
      >
        <Form form={bindForm} layout="vertical">
          <Form.Item name="group_ids" label="选择分组（可多选）">
            <Checkbox.Group style={{ width: '100%' }}>
              <Space wrap>
                {groups.map((g) => (
                  <Checkbox key={g.id} value={g.id}>
                    {g.name}
                  </Checkbox>
                ))}
              </Space>
            </Checkbox.Group>
          </Form.Item>
          <Form.Item name="tag_ids" label="选择标签（可多选）">
            <Checkbox.Group style={{ width: '100%' }}>
              <Space wrap>
                {tags.map((t) => (
                  <Checkbox key={t.id} value={t.id}>
                    <Tag color={t.color}>{t.name}</Tag>
                  </Checkbox>
                ))}
              </Space>
            </Checkbox.Group>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default BusinessPagesPanel;
