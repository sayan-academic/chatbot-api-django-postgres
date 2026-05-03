# Create your models here.
from django.db import models

from django.contrib.auth.models import User

class ChatMessage(models.Model):
    """
    Stores individual message turns between the User and the AI.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Add this new line:
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'AI Assistant'),
    ]

    # Identifies who sent the message
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES
    )
    
    # The actual text content
    content = models.TextField()
    
    # Automatically capture the exact time of the interaction
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Crucial for the 'Sliding Window' logic: always fetch in order
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"{self.role.upper()} - {self.created_at}"