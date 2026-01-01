import json
import uuid
from django.test import TestCase, APIClient
from django.utils import timezone
from rest_framework import status
from support.models import SupportConversation, SupportMessage


class EscalationFlowTests(TestCase):
    """Test the complete escalation flow from start to resolution"""

    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()

    def test_conversation_creation(self):
        """Test creating a new conversation"""
        response = self.client.post('/api/v1/conversations/', {
            'user_id': 'test_user_123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('conversation_id', response.data)
        self.assertEqual(response.data['user_id'], 'test_user_123')
        self.assertEqual(response.data['status'], 'open')  # Should be 'open' by default

    def test_user_message_gets_ai_response(self):
        """Test that user message gets AI response in normal conversation"""
        # Create conversation
        conversation = SupportConversation.objects.create(user_id='test_user')
        conversation_id = conversation.session_id

        # Send user message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Where is my order?'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('ai_response', response.data)
        self.assertEqual(response.data['sender'], 'user')
        self.assertEqual(response.data['ai_response']['sender'], 'ai')

    def test_escalation_intent_blocks_ai(self):
        """Test that escalation intent blocks AI response"""
        # Create conversation
        conversation = SupportConversation.objects.create(user_id='test_user')
        conversation_id = conversation.session_id

        # Send escalation message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'I want to talk to a human agent'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detected_intent'], 'escalation')

        # AI response should NOT be generated
        self.assertNotIn('ai_response', response.data)

        # Verify conversation is escalated
        conversation.refresh_from_db()
        self.assertTrue(conversation.escalated)
        self.assertEqual(conversation.status, 'escalated')
        self.assertIsNotNone(conversation.escalated_at)
        self.assertIn('human agent', conversation.escalation_reason)

    def test_manually_escalate_conversation(self):
        """Test manually escalating a conversation via API"""
        # Create conversation
        conversation = SupportConversation.objects.create(user_id='test_user')
        conversation_id = conversation.session_id

        # Manually escalate
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/escalate/', {
            'reason': 'Complex issue requiring human intervention'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'escalated')
        self.assertTrue(response.data['escalated'])

        # Verify in database
        conversation.refresh_from_db()
        self.assertTrue(conversation.escalated)
        self.assertEqual(conversation.status, 'escalated')
        self.assertIsNotNone(conversation.escalated_at)
        self.assertEqual(conversation.escalation_reason, 'Complex issue requiring human intervention')

    def test_cannot_escalate_already_escalated_conversation(self):
        """Test that already escalated conversation cannot be escalated again"""
        # Create escalated conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='escalated',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Try to escalate again
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/escalate/', {
            'reason': 'Another reason'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already escalated', response.data['error'])

    def test_assign_agent_to_escalated_conversation(self):
        """Test assigning an agent to escalated conversation"""
        # Create escalated conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='escalated',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Assign agent
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/assign/', {
            'agent_id': 'agent_123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'assigned')
        self.assertEqual(response.data['assigned_agent'], 'agent_123')

        # Verify in database
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, 'assigned')
        self.assertEqual(conversation.assigned_agent, 'agent_123')

    def test_cannot_assign_agent_to_non_escalated_conversation(self):
        """Test that agent cannot be assigned to non-escalated conversation"""
        # Create open conversation
        conversation = SupportConversation.objects.create(user_id='test_user')
        conversation_id = conversation.session_id

        # Try to assign agent
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/assign/', {
            'agent_id': 'agent_123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be escalated', response.data['error'])

    def test_agent_can_send_message_to_assigned_conversation(self):
        """Test that agent can send messages to assigned conversation"""
        # Create assigned conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='assigned',
            assigned_agent='agent_123',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Send agent message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
            'message': 'Hello, I am here to help you with your issue.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sender'], 'agent')
        self.assertEqual(response.data['message'], 'Hello, I am here to help you with your issue.')

        # Verify message is in database
        message = SupportMessage.objects.get(id=response.data['message_id'])
        self.assertEqual(message.sender, 'agent')
        self.assertEqual(message.conversation, conversation)

    def test_agent_can_send_message_to_escalated_conversation(self):
        """Test that agent can send messages to escalated (but not yet assigned) conversation"""
        # Create escalated conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='escalated',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Send agent message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
            'message': 'Hello, I am here to help you with your issue.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sender'], 'agent')

    def test_cannot_send_agent_message_to_open_conversation(self):
        """Test that agent cannot send messages to open conversation"""
        # Create open conversation
        conversation = SupportConversation.objects.create(user_id='test_user')
        conversation_id = conversation.session_id

        # Try to send agent message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
            'message': 'Test message'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be assigned or escalated', response.data['error'])

    def test_resolve_conversation(self):
        """Test resolving a conversation"""
        # Create assigned conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='assigned',
            assigned_agent='agent_123',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Resolve conversation
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/resolve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'resolved')
        self.assertIn('resolved_at', response.data)

        # Verify in database
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, 'resolved')
        self.assertIsNotNone(conversation.resolved_at)
        self.assertIsNotNone(conversation.ended_at)

    def test_cannot_resolve_already_resolved_conversation(self):
        """Test that already resolved conversation cannot be resolved again"""
        # Create resolved conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='resolved',
            resolved_at=timezone.now(),
            ended_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Try to resolve again
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/resolve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already resolved', response.data['error'])

    def test_ai_blocked_after_escalation(self):
        """Test that AI is completely blocked after escalation"""
        # Create conversation
        conversation = SupportConversation.objects.create(user_id='test_user')
        conversation_id = conversation.session_id

        # Send first message - should get AI response
        response1 = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Hello'
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertIn('ai_response', response1.data)

        # Escalate conversation
        conversation.status = 'escalated'
        conversation.escalated = True
        conversation.escalated_at = timezone.now()
        conversation.save()

        # Send second message - should NOT get AI response
        response2 = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Where is my order?'
        })
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('ai_response', response2.data)

    def test_ai_blocked_after_assignment(self):
        """Test that AI is blocked after agent assignment"""
        # Create assigned conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='assigned',
            assigned_agent='agent_123',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Send user message - should NOT get AI response
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Where is my order?'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('ai_response', response.data)

    def test_ai_blocked_after_resolution(self):
        """Test that AI is blocked after resolution"""
        # Create resolved conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='resolved',
            resolved_at=timezone.now(),
            ended_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Send user message - should NOT get AI response
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Where is my order?'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('ai_response', response.data)

    def test_complete_escalation_flow(self):
        """Test the complete escalation flow from creation to resolution"""
        # 1. Create conversation
        conv_response = self.client.post('/api/v1/conversations/', {
            'user_id': 'test_user_456'
        })
        conversation_id = conv_response.data['conversation_id']
        self.assertEqual(conv_response.status_code, status.HTTP_201_CREATED)

        # 2. User sends message - gets AI response
        msg1_response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Where is my order?'
        })
        self.assertEqual(msg1_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('ai_response', msg1_response.data)

        # 3. User requests escalation
        escalate_response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'I want to talk to a human agent'
        })
        self.assertEqual(escalate_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(escalate_response.data['detected_intent'], 'escalation')
        self.assertNotIn('ai_response', escalate_response.data)

        # 4. Verify conversation is escalated
        conversation = SupportConversation.objects.get(session_id=conversation_id)
        self.assertTrue(conversation.escalated)
        self.assertEqual(conversation.status, 'escalated')

        # 5. Assign agent
        assign_response = self.client.post(f'/api/v1/conversations/{conversation_id}/assign/', {
            'agent_id': 'agent_789'
        })
        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        self.assertEqual(assign_response.data['status'], 'assigned')

        # 6. Agent sends message
        agent_response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
            'message': 'Hello, how can I help you today?'
        })
        self.assertEqual(agent_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(agent_response.data['sender'], 'agent')

        # 7. User sends another message - should NOT get AI response
        msg2_response = self.client.post(f'/api/v1/conversations/{conversation_id}/messages/', {
            'message': 'Thanks for your help'
        })
        self.assertEqual(msg2_response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('ai_response', msg2_response.data)

        # 8. Resolve conversation
        resolve_response = self.client.post(f'/api/v1/conversations/{conversation_id}/resolve/')
        self.assertEqual(resolve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(resolve_response.data['status'], 'resolved')

        # 9. Verify final state
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, 'resolved')
        self.assertIsNotNone(conversation.resolved_at)
        self.assertIsNotNone(conversation.ended_at)

        # 10. Verify message count
        self.assertEqual(SupportMessage.objects.filter(conversation=conversation).count(), 4)

    def test_agent_message_validation_empty_message(self):
        """Test that empty agent messages are rejected"""
        # Create escalated conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='escalated',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Try to send empty message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
            'message': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be empty', str(response.data))

    def test_agent_message_validation_whitespace_only(self):
        """Test that whitespace-only messages are rejected"""
        # Create escalated conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='escalated',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Try to send whitespace-only message
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
            'message': '   '
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be empty', str(response.data))

    def test_assign_agent_validation_missing_agent_id(self):
        """Test that agent assignment without agent_id is rejected"""
        # Create escalated conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='escalated',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Try to assign without agent_id
        response = self.client.post(f'/api/v1/conversations/{conversation_id}/assign/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('agent_id', response.data)

    def test_conversation_status_lifecycle(self):
        """Test that conversation status follows the correct lifecycle"""
        conversation = SupportConversation.objects.create(user_id='test_user')
        self.assertEqual(conversation.status, 'open')

        # Escalate
        conversation.status = 'escalated'
        conversation.escalated = True
        conversation.escalated_at = timezone.now()
        conversation.save()
        self.assertEqual(conversation.status, 'escalated')

        # Assign
        conversation.status = 'assigned'
        conversation.assigned_agent = 'agent_123'
        conversation.save()
        self.assertEqual(conversation.status, 'assigned')

        # Resolve
        conversation.status = 'resolved'
        conversation.resolved_at = timezone.now()
        conversation.ended_at = timezone.now()
        conversation.save()
        self.assertEqual(conversation.status, 'resolved')

    def test_conversation_serializer_includes_new_fields(self):
        """Test that conversation serializer includes new fields"""
        # Create conversation with all fields
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            language='en',
            status='open'
        )
        conversation_id = conversation.session_id

        # Get conversation details
        response = self.client.get(f'/api/v1/conversations/{conversation_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new fields are included
        self.assertIn('status', response.data)
        self.assertIn('assigned_agent', response.data)
        self.assertIn('escalated_at', response.data)
        self.assertIn('resolved_at', response.data)
        self.assertEqual(response.data['status'], 'open')

    def test_multiple_agent_messages(self):
        """Test that multiple agent messages can be sent"""
        # Create assigned conversation
        conversation = SupportConversation.objects.create(
            user_id='test_user',
            escalated=True,
            status='assigned',
            assigned_agent='agent_123',
            escalated_at=timezone.now()
        )
        conversation_id = conversation.session_id

        # Send multiple agent messages
        messages = [
            'Hello, how can I help?',
            'I understand your issue.',
            'Let me check that for you.'
        ]

        for msg in messages:
            response = self.client.post(f'/api/v1/conversations/{conversation_id}/agent/messages/', {
                'message': msg
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['sender'], 'agent')

        # Verify all messages are in database
        agent_messages = SupportMessage.objects.filter(
            conversation=conversation,
            sender='agent'
        )
        self.assertEqual(agent_messages.count(), 3)
