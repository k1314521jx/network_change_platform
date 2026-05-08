const STATUS_MAP = {
  pending:     { label: '执行中', type: 'warning' },
  success:     { label: '成功',   type: 'success' },
  failed:      { label: '失败',   type: 'danger' },
  approved:    { label: '已通过', type: 'success' },
  rejected:    { label: '已驳回', type: 'danger' },
  review_pending: { label: '待审核', type: 'warning' },
  // AI审核状态
  ai_pending:   { label: '待审核', type: 'warning' },
  reviewing:    { label: '审核中', type: 'primary' },
  reviewed:     { label: '已审核', type: 'success' },
  ai_failed:    { label: '审核失败', type: 'danger' },
}

/**
 * 状态标签 composable
 * @returns {{ getStatusTag: (status: string) => { label: string, type: string } }}
 */
export function useStatusTag() {
  function getStatusTag(status) {
    return STATUS_MAP[status] || { label: status, type: 'info' }
  }

  return { getStatusTag }
}
