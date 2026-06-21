import {
  Button,
  Card,
  Checkbox,
  Form,
  Image,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  Tooltip,
  Upload,
  message,
} from 'antd';
import { CopyOutlined, DownloadOutlined, QrcodeOutlined, ReloadOutlined } from '@ant-design/icons';
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
  const [qrcodeOpen, setQrcodeOpen] = useState(false);
  const [editingPage, setEditingPage] = useState(null);
  const [bindingPage, setBindingPage] = useState(null);
  const [qrcodePage, setQrcodePage] = useState(null);
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

  const openQrcode = async (page) => {
    setQrcodePage(page);
    setQrcodeOpen(true);
    if (!page.qrcode_url) {
      try {
        const { data } = await http.post(`/api/admin/pages/${page.id}/qrcode/refresh`);
        setPages((prev) => prev.map((p) => (p.id === page.id ? data.data : p)));
        setQrcodePage(data.data);
      } catch (error) {
        message.error(extractErrorMessage(error));
      }
    }
  };

  const copyShareUrl = async (page) => {
    try {
      let shareUrl = page.share_url;
      if (!shareUrl) {
        const { data } = await http.get(`/api/admin/pages/${page.id}/share-url`);
        shareUrl = data.data.share_url;
      }
      await navigator.clipboard.writeText(shareUrl);
      message.success('分享链接已复制到剪贴板');
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const downloadQrcode = async (page) => {
    try {
      const response = await http.get(`/api/admin/pages/${page.id}/qrcode`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${page.name}_qrcode.png`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success('二维码下载成功');
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const refreshQrcode = async (page) => {
    try {
      const { data } = await http.post(`/api/admin/pages/${page.id}/qrcode/refresh`);
      setPages((prev) => prev.map((p) => (p.id === page.id ? data.data : p)));
      if (qrcodePage && qrcodePage.id === page.id) {
        setQrcodePage(data.data);
      }
      message.success('二维码已刷新');
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
      title: '访问二维码',
      dataIndex: 'qrcode_url',
      width: 140,
      render: (value, record) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          {value ? (
            <Image
              src={value}
              alt={`${record.name} 二维码`}
              width={80}
              height={80}
              style={{ cursor: 'pointer', border: '1px solid #f0f0f0', borderRadius: 4 }}
              preview={false}
              onClick={() => openQrcode(record)}
              fallback={
                <div
                  style={{
                    width: 80,
                    height: 80,
                    border: '1px dashed #d9d9d9',
                    borderRadius: 4,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#bfbfbf',
                    fontSize: 12,
                  }}
                >
                  加载失败
                </div>
              }
            />
          ) : (
            <div
              style={{
                width: 80,
                height: 80,
                border: '1px dashed #d9d9d9',
                borderRadius: 4,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#8c9ab5',
                fontSize: 12,
                cursor: 'pointer',
              }}
              onClick={() => refreshQrcode(record)}
              title="点击生成二维码"
            >
              <ReloadOutlined style={{ fontSize: 16, marginBottom: 2 }} />
              点我生成
            </div>
          )}
          <Space size={4}>
            <Tooltip title="下载二维码">
              <Button
                type="link"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => downloadQrcode(record)}
                style={{ padding: 0 }}
              />
            </Tooltip>
            <Tooltip title="复制分享链接">
              <Button
                type="link"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => copyShareUrl(record)}
                style={{ padding: 0 }}
              />
            </Tooltip>
            <Tooltip title={value ? '查看大图' : '生成并查看'}>
              <Button
                type="link"
                size="small"
                icon={<QrcodeOutlined />}
                onClick={() => openQrcode(record)}
                style={{ padding: 0 }}
              />
            </Tooltip>
          </Space>
        </Space>
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
      width: 320,
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
          <Button size="small" icon={<QrcodeOutlined />} onClick={() => openQrcode(record)}>
            二维码
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
      <Table rowKey="id" loading={loading} columns={columns} dataSource={pages} scroll={{ x: 1900 }} />

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

      <Modal
        title={qrcodePage ? `访问二维码 - ${qrcodePage.name}` : '访问二维码'}
        open={qrcodeOpen}
        onCancel={() => {
          setQrcodeOpen(false);
          setQrcodePage(null);
        }}
        footer={[
          <Button
            key="refresh"
            icon={<ReloadOutlined />}
            onClick={() => qrcodePage && refreshQrcode(qrcodePage)}
          >
            刷新二维码
          </Button>,
          <Button
            key="copy"
            icon={<CopyOutlined />}
            onClick={() => qrcodePage && copyShareUrl(qrcodePage)}
          >
            复制分享链接
          </Button>,
          <Button
            key="download"
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => qrcodePage && downloadQrcode(qrcodePage)}
          >
            下载二维码
          </Button>,
        ]}
        width={480}
        destroyOnClose
      >
        {qrcodePage && (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            {qrcodePage.qrcode_url ? (
              <Image
                src={qrcodePage.qrcode_url}
                alt={`${qrcodePage.name} 访问二维码`}
                width={260}
                height={260}
                style={{ border: '1px solid #f0f0f0', borderRadius: 8, padding: 8 }}
                preview={false}
                fallback={
                  <div
                    style={{
                      width: 260,
                      height: 260,
                      border: '1px dashed #faad14',
                      borderRadius: 8,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#faad14',
                      margin: '0 auto',
                      gap: 8,
                    }}
                  >
                    <ReloadOutlined style={{ fontSize: 32 }} />
                    <div style={{ fontSize: 13 }}>图片加载失败，点击下方按钮刷新</div>
                  </div>
                }
              />
            ) : (
              <div
                style={{
                  width: 260,
                  height: 260,
                  border: '1px dashed #1890ff',
                  borderRadius: 8,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#1890ff',
                  margin: '0 auto',
                  gap: 8,
                }}
              >
                <ReloadOutlined spin style={{ fontSize: 32 }} />
                <div style={{ fontSize: 13 }}>二维码生成中，请稍候...</div>
              </div>
            )}
            <div style={{ marginTop: 20 }}>
              <div style={{ color: '#666', fontSize: 13, marginBottom: 6 }}>分享链接：</div>
              <Input
                value={qrcodePage.share_url || qrcodePage.route_path || ''}
                readOnly
                style={{ fontFamily: 'monospace', fontSize: 12 }}
                suffix={
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => copyShareUrl(qrcodePage)}
                  />
                }
              />
            </div>
            <div style={{ marginTop: 12, color: '#999', fontSize: 12 }}>
              扫描二维码或复制链接即可访问该业务页面
            </div>
          </div>
        )}
      </Modal>
    </Card>
  );
}

export default BusinessPagesPanel;
