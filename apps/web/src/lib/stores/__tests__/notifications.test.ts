/**
 * Unit tests for notifications store.
 * 
 * Example test file demonstrating testing patterns.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import {
  notificationsStore,
  addNotification,
  removeNotification,
  clearNotifications,
  notify,
} from '../notifications';

describe('notifications store', () => {
  beforeEach(() => {
    clearNotifications();
  });

  it('should initialize with empty list', () => {
    const state = get(notificationsStore);
    expect(state.list).toEqual([]);
  });

  it('should add a notification', () => {
    addNotification({
      type: 'success',
      title: 'Test',
      message: 'Test message',
    });

    const state = get(notificationsStore);
    expect(state.list).toHaveLength(1);
    expect(state.list[0].title).toBe('Test');
    expect(state.list[0].type).toBe('success');
  });

  it('should remove a notification by id', () => {
    const id = addNotification({
      type: 'info',
      title: 'Test',
    });

    removeNotification(id);

    const state = get(notificationsStore);
    expect(state.list).toHaveLength(0);
  });

  it('should clear all notifications', () => {
    addNotification({ type: 'success', title: 'Test 1' });
    addNotification({ type: 'error', title: 'Test 2' });

    clearNotifications();

    const state = get(notificationsStore);
    expect(state.list).toHaveLength(0);
  });

  describe('notify helpers', () => {
    it('notify.success should create success notification', () => {
      notify.success('Success', 'Operation completed');

      const state = get(notificationsStore);
      expect(state.list[0].type).toBe('success');
      expect(state.list[0].title).toBe('Success');
    });

    it('notify.error should create error notification', () => {
      notify.error('Error', 'Something went wrong');

      const state = get(notificationsStore);
      expect(state.list[0].type).toBe('error');
      expect(state.list[0].duration).toBe(7000); // Errors stay longer
    });

    it('notify.warning should create warning notification', () => {
      notify.warning('Warning', 'Be careful');

      const state = get(notificationsStore);
      expect(state.list[0].type).toBe('warning');
    });

    it('notify.info should create info notification', () => {
      notify.info('Info', 'Here is some information');

      const state = get(notificationsStore);
      expect(state.list[0].type).toBe('info');
    });
  });
});





























