from rest_framework import serializers
from alumni.models import AlumniEvent, EventAttendance
from alumni.models.alumni import Alumni
from .alumni import AlumniMinimalSerializer


# AlumniEvent serializers
class AlumniEventMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for alumni events."""

    class Meta:
        model = AlumniEvent
        fields = ["id", "title", "event_date", "location"]
        read_only_fields = fields


class AlumniEventCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an alumni event."""

    class Meta:
        model = AlumniEvent
        fields = "__all__"

    def create(self, validated_data) -> AlumniEvent:
        from alumni.services.event import AlumniEventService

        return AlumniEventService.create_event(**validated_data)


class AlumniEventUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an alumni event."""

    class Meta:
        model = AlumniEvent
        fields = ["title", "description", "event_date", "location", "max_attendees", "meeting_link", "registration_deadline"]

    def update(self, instance, validated_data) -> AlumniEvent:
        from alumni.services.event import AlumniEventService

        return AlumniEventService.update_event(instance, validated_data)


class AlumniEventDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an alumni event."""

    class Meta:
        model = AlumniEvent
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


# EventAttendance serializers
class EventAttendanceMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for event attendance."""

    alumni = AlumniMinimalSerializer(read_only=True)
    event = AlumniEventMinimalSerializer(read_only=True)

    class Meta:
        model = EventAttendance
        fields = ["id", "alumni", "event", "rsvp_status", "attended"]
        read_only_fields = fields


class EventAttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an event attendance record."""

    alumni_id = serializers.PrimaryKeyRelatedField(
        queryset=Alumni.objects.all(), source="alumni"
    )
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=AlumniEvent.objects.all(), source="event"
    )

    class Meta:
        model = EventAttendance
        fields = ["alumni_id", "event_id", "rsvp_status", "attended", "notes"]

    def create(self, validated_data) -> EventAttendance:
        from alumni.services.event import EventAttendanceService

        return EventAttendanceService.create_attendance(**validated_data)


class EventAttendanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an event attendance record."""

    class Meta:
        model = EventAttendance
        fields = ["rsvp_status", "attended", "notes"]

    def update(self, instance, validated_data) -> EventAttendance:
        from alumni.services.event import EventAttendanceService

        return EventAttendanceService.update_rsvp(instance, validated_data.get('rsvp_status'))


class EventAttendanceDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for an event attendance record."""

    alumni = AlumniMinimalSerializer(read_only=True)
    event = AlumniEventMinimalSerializer(read_only=True)

    class Meta:
        model = EventAttendance
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "checked_in_at"]